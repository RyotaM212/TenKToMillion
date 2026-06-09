from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

from app.config import get_settings
from app.db import fetch_all, fetch_one, init_db
from app.llm.analyst_service import AnalystService
from app.llm.schemas import AnalystClientResult
from app.models import MarketSnapshot
from app.scheduler.jobs import build_scheduler
from app.services import run_analysis, run_optimization, run_paper_trade, run_screening, set_app_state
from app.strategies import build_strategies
from app.trading.capital_manager import CapitalManager
from app.trading.live_broker_interface import LiveBrokerInterface
from app.trading.paper_broker import PaperBroker
from app.trading.risk_guard import RiskGuard
from app.llm.response_parser import ResponseParser
from app.models import Candidate, OrderRequest, StrategyParams


class FakeCollector:
    def fetch_symbols(self) -> list[dict[str, str]]:
        return [{"symbol": snapshot.symbol, "symbol_name": snapshot.symbol_name} for snapshot in self.fetch_ranking()]

    def fetch_daily_prices(self, symbol: str) -> list[MarketSnapshot]:
        return [snapshot for snapshot in self.fetch_ranking() if snapshot.symbol == symbol]

    def fetch_intraday_prices(self, symbol: str) -> list[MarketSnapshot]:
        return self.fetch_daily_prices(symbol)

    def fetch_ranking(self) -> list[MarketSnapshot]:
        return [
            MarketSnapshot(
                symbol="2160",
                symbol_name="ジーエヌアイグループ",
                snapshot_time=datetime.fromisoformat(f"{date.today().isoformat()}T09:10:00"),
                price=100.0,
                volume=2_000_000,
                vwap=99.0,
                open=101.0,
                high=118.0,
                low=98.0,
                close=112.0,
                previous_close=95.0,
                news_score=0.8,
            ),
            MarketSnapshot(
                symbol="4565",
                symbol_name="ネクセラファーマ",
                snapshot_time=datetime.fromisoformat(f"{date.today().isoformat()}T09:10:00"),
                price=120.0,
                volume=1_400_000,
                vwap=118.0,
                open=119.0,
                high=142.0,
                low=118.0,
                close=136.0,
                previous_close=110.0,
                news_score=0.6,
            ),
            MarketSnapshot(
                symbol="6920",
                symbol_name="レーザーテック",
                snapshot_time=datetime.fromisoformat(f"{date.today().isoformat()}T09:10:00"),
                price=150.0,
                volume=1_800_000,
                vwap=145.0,
                open=148.0,
                high=178.0,
                low=146.0,
                close=170.0,
                previous_close=135.0,
                news_score=0.5,
            ),
        ]


class FakeAnalystClient:
    model_name = "test-analyst"

    def analyze(self, prompt: str) -> AnalystClientResult:
        output = {
            "summary_text": "テスト用の実績分析です。",
            "win_patterns": ["出来高と上昇率が同時に強い候補が有効でした。"],
            "lose_patterns": ["該当なし。"],
            "risk_notes": ["本番注文は無効で、ペーパートレードのみです。"],
            "improvement_suggestions": ["利確幅を少し狭める検証を行う。"],
            "next_day_hypotheses": ["高出来高の寄り後継続銘柄を優先する。"],
            "proposed_params": {
                "entry_start_time": "09:15",
                "entry_end_time": "10:20",
                "take_profit_rate": 0.1,
                "stop_loss_rate": 0.05,
                "volume_spike_threshold": 3.0,
                "breakout_threshold": 0.01,
                "vwap_exit_enabled": True,
            },
            "confidence_score": 0.7,
        }
        return AnalystClientResult(model_name=self.model_name, content=json.dumps(output, ensure_ascii=False), token_usage={"total_tokens": 1})


class FailingCollector:
    def fetch_ranking(self) -> list[MarketSnapshot]:
        raise RuntimeError("external market data should not be required after screening snapshots are persisted")


class PipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        os.environ["DATABASE_PATH"] = str(Path(self.tmpdir.name) / "test.db")
        os.environ["DATA_SOURCE"] = "jquants"
        os.environ["JQUANTS_API_KEY"] = "test-key"
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["SCHEDULER_ENABLED"] = "true"
        get_settings.cache_clear()
        init_db()
        set_app_state("data_source", "jquants")

    def test_automated_pipeline_creates_trade_reports_and_experiments(self) -> None:
        with patch("app.services.get_collector", return_value=FakeCollector()):
            self.assertGreater(run_screening()["created"], 0)
        with patch("app.services.get_collector", return_value=FailingCollector()):
            self.assertGreater(run_screening()["created"], 0)
        with patch("app.services.get_collector", return_value=FailingCollector()):
            self.assertGreater(run_paper_trade()["created"], 0)

        self.assertEqual(run_analysis()["created"], 12)
        self.assertEqual(run_optimization()["created"], 4)

        self.assertGreater(len(fetch_all("SELECT * FROM candidates")), 0)
        self.assertGreater(len(fetch_all("SELECT * FROM paper_trades")), 0)
        self.assertEqual(len(fetch_all("SELECT * FROM daily_reports")), 12)
        self.assertEqual(len(fetch_all("SELECT * FROM strategy_experiments")), 4)
        self.assertGreater(len(fetch_all("SELECT * FROM strategy_params")), 0)

    def test_llm_analysis_requires_real_client_but_can_be_injected_for_tests(self) -> None:
        with patch("app.services.get_collector", return_value=FakeCollector()):
            run_screening()
            run_paper_trade()
        run_analysis()

        with patch("app.llm.analyst_service.build_analyst_client", return_value=FakeAnalystClient()):
            report = AnalystService().run_daily_analysis(date.today())

        self.assertEqual(report.model_name, "test-analyst")
        self.assertEqual(fetch_one("SELECT status FROM llm_analysis_runs ORDER BY id DESC LIMIT 1")["status"], "success")
        self.assertGreater(len(fetch_all("SELECT * FROM strategy_experiments")), 0)

    def test_scheduler_contains_full_daily_automation(self) -> None:
        scheduler = build_scheduler()
        job_ids = {job.id for job in scheduler.get_jobs()}
        self.assertEqual(
            job_ids,
            {
                "screening",
                "paper_trade",
                "stop_new_entries",
                "force_exit_all_positions",
                "daily_analysis",
                "llm_daily_analysis",
                "llm_backtest_proposals",
                "optimization",
            },
        )

    def test_security_boundaries_reject_mock_and_live_trading(self) -> None:
        with self.assertRaises(ValueError):
            set_app_state("data_source", "mock")
        with self.assertRaises(NotImplementedError):
            LiveBrokerInterface().buy("2160", 100)
        with self.assertRaises(NotImplementedError):
            LiveBrokerInterface().sell("2160", 100)

    def test_capital_manager_modes(self) -> None:
        manager = CapitalManager(10_000)
        self.assertEqual(manager.buying_power("YOLO_MODE", 500, 0), 10_500)
        self.assertEqual(manager.buying_power("LOCK_PROFIT_MODE", 500, 250), 10_250)
        self.assertEqual(manager.locked_profit_after_trade("LOCK_PROFIT_MODE", 0, 800), 400)
        self.assertEqual(manager.quantity_for(10_000, 120), 83)

    def test_risk_guard_order_rules(self) -> None:
        guard = RiskGuard()
        cash = {"cash": 10_000}
        self.assertEqual(guard.validate_order(OrderRequest("buy", "2160", 10, 100), cash, [])[0], True)
        self.assertEqual(guard.validate_order(OrderRequest("buy", "2160", 101, 100), cash, [])[0], False)
        self.assertEqual(guard.validate_order(OrderRequest("sell", "2160", 1, 100), cash, [])[0], False)
        self.assertEqual(guard.validate_order(OrderRequest("buy", "2160", 1, 100, order_type="cash", leverage=2), cash, [])[0], False)
        self.assertEqual(guard.validate_order(OrderRequest("buy", "2160", 1, 100, allow_overnight=True), cash, [])[0], False)

    def test_paper_broker_and_strategy_entry_use_params(self) -> None:
        snapshot = FakeCollector().fetch_ranking()[0]
        candidate = Candidate(
            trade_date=date.today().isoformat(),
            symbol=snapshot.symbol,
            symbol_name=snapshot.symbol_name,
            score=80,
            strategy_name="VolumeStrategy",
            volume_spike_score=1,
            price_change_score=1,
            gap_up_score=1,
            volatility_score=1,
            news_score=0,
            liquidity_score=1,
            selected_reason="test",
        )
        strategy = build_strategies()[0]
        self.assertTrue(strategy.can_enter(snapshot, candidate.score))
        result = PaperBroker(10_000, persist=False).run_for_candidate(
            "YOLO_MODE",
            candidate,
            snapshot,
            StrategyParams("VolumeStrategy", take_profit_rate=0.1),
            0,
            0,
            False,
        )
        self.assertIsNotNone(result)
        self.assertGreater(float(result["pnl"]), 0)

    def test_response_parser_rejects_invalid_and_forbidden_outputs(self) -> None:
        parser = ResponseParser()
        with self.assertRaises(ValueError):
            parser.parse("{}")
        forbidden = {
            "summary_text": "x",
            "win_patterns": [],
            "lose_patterns": [],
            "risk_notes": ["信用取引を使う"],
            "improvement_suggestions": [],
            "next_day_hypotheses": [],
            "proposed_params": {},
            "confidence_score": 0.5,
        }
        with self.assertRaises(ValueError):
            parser.parse(json.dumps(forbidden, ensure_ascii=False))
