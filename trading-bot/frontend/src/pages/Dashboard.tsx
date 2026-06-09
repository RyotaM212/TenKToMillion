import { Activity, AlertCircle, BarChart3, Bot, Database, Play, RefreshCw, ShieldCheck, Wallet } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import type { DashboardData, DataSourceComparison, LlmCostHistory } from "../api";
import { fetchDashboard, fetchDataSourceComparison, fetchLlmCosts, postBotAction, postLlmAction, postState } from "../api";
import { CandidateList } from "../components/CandidateList";
import { DataSourceComparisonPanel } from "../components/DataSourceComparisonPanel";
import { EquityCurve } from "../components/EquityCurve";
import { LlmAnalystPanel } from "../components/LlmAnalystPanel";
import { ModeComparison } from "../components/ModeComparison";
import { OpenAICostPanel } from "../components/OpenAICostPanel";
import { StrategyComparison } from "../components/StrategyComparison";
import { StrategyParamsPanel } from "../components/StrategyParamsPanel";
import { TradeTable } from "../components/TradeTable";

const emptyDashboard: DashboardData = {
  current_asset: 10000,
  buying_power: 10000,
  locked_profit: 0,
  today_pnl: 0,
  total_pnl: 0,
  win_rate: 0,
  max_drawdown: 0,
  mode: "YOLO_MODE",
  active_strategy: "HybridStrategy",
  data_source: "jquants",
  candidates: [],
  positions: [],
  trades: [],
  reports: [],
  experiments: [],
  llm_report: null,
};

export function Dashboard() {
  const [data, setData] = useState<DashboardData>(emptyDashboard);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [costs, setCosts] = useState<LlmCostHistory | null>(null);
  const [comparison, setComparison] = useState<DataSourceComparison | null>(null);

  async function load() {
    setError(null);
    try {
      const [dashboard, costHistory] = await Promise.all([fetchDashboard(), fetchLlmCosts()]);
      setData(dashboard);
      setCosts(costHistory);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "不明なエラーが発生しました");
    } finally {
      setLoading(false);
    }
  }

  async function run(action: "run-screening" | "run-paper-trade" | "run-analysis" | "run-optimization") {
    setRunning(action);
    setError(null);
    try {
      await postBotAction(action);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "実行に失敗しました");
    } finally {
      setRunning(null);
    }
  }

  async function runLlm(action: "run-daily-analysis" | "backtest-proposals") {
    setRunning(action);
    setError(null);
    try {
      await postLlmAction(action);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "AI分析の実行に失敗しました");
    } finally {
      setRunning(null);
    }
  }

  async function updateState(endpoint: "set-mode" | "set-data-source" | "set-strategy", value: string) {
    setRunning(endpoint);
    setError(null);
    try {
      await postState(endpoint, value);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "設定の更新に失敗しました");
    } finally {
      setRunning(null);
    }
  }

  async function compareSources() {
    setRunning("compare-data-sources");
    setError(null);
    try {
      setComparison(await fetchDataSourceComparison());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "データソース比較に失敗しました");
    } finally {
      setRunning(null);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const isBusy = running !== null;

  return (
    <main className="appShell">
      <header className="topbar">
        <div>
          <div className="topbarBrand">
            <img className="appLogo" src="/app-icon.svg" alt="" aria-hidden="true" />
            <div>
              <h1>TenKToMillion</h1>
              <span className="liveTag">Paper</span>
            </div>
          </div>
          <p>現物・空売りなし・レバレッジなし。実注文は無効化されています。</p>
        </div>
        <div className="topbarActions">
          <button className="iconButton" onClick={() => void load()} title="更新" type="button" disabled={isBusy}>
            <RefreshCw size={15} />
          </button>
        </div>
      </header>

      <section className="statusStrip">
        <Metric icon={<Wallet size={15} />} label="現在資産" value={`¥${data.current_asset.toLocaleString()}`} />
        <Metric icon={<Activity size={15} />} label="本日の損益" value={`¥${data.today_pnl.toLocaleString()}`} tone={data.today_pnl >= 0 ? "positive" : "negative"} />
        <Metric icon={<BarChart3 size={15} />} label="累計損益" value={`¥${data.total_pnl.toLocaleString()}`} tone={data.total_pnl >= 0 ? "positive" : "negative"} />
        <Metric icon={<ShieldCheck size={15} />} label="ロック済み利益" value={`¥${data.locked_profit.toLocaleString()}`} />
        <Metric icon={<Database size={15} />} label="データソース" value={data.data_source} />
        <Metric icon={<Bot size={15} />} label="資金管理モード" value={data.mode} />
      </section>

      <section className="actionBar">
        <ActionButton label="候補生成" action="run-screening" running={running} onRun={run} />
        <ActionButton label="ペーパー実行" action="run-paper-trade" running={running} onRun={run} />
        <ActionButton label="日次分析" action="run-analysis" running={running} onRun={run} />
        <ActionButton label="改善案生成" action="run-optimization" running={running} onRun={run} />
        <div className="actionDivider" />
        <LlmActionButton label="AI分析実行" action="run-daily-analysis" running={running} onRun={runLlm} />
        <LlmActionButton label="AI提案検証" action="backtest-proposals" running={running} onRun={runLlm} />
      </section>

      <section className="settingsBar">
        <label>
          データソース
          <select disabled={isBusy} value={data.data_source} onChange={(e) => void updateState("set-data-source", e.currentTarget.value)}>
            <option value="yahoo">Yahoo系</option>
            <option value="jquants">J-Quants</option>
          </select>
        </label>
        <label>
          資金管理
          <select disabled={isBusy} value={data.mode} onChange={(e) => void updateState("set-mode", e.currentTarget.value)}>
            <option value="YOLO_MODE">YOLO_MODE</option>
            <option value="LOCK_PROFIT_MODE">LOCK_PROFIT_MODE</option>
            <option value="ONE_SHOT_MODE">ONE_SHOT_MODE</option>
          </select>
        </label>
        <label>
          表示戦略
          <select disabled={isBusy} value={data.active_strategy} onChange={(e) => void updateState("set-strategy", e.currentTarget.value)}>
            <option value="VolumeStrategy">VolumeStrategy</option>
            <option value="MomentumStrategy">MomentumStrategy</option>
            <option value="NewsStrategy">NewsStrategy</option>
            <option value="HybridStrategy">HybridStrategy</option>
          </select>
        </label>
      </section>

      {error && (
        <div className="errorBox">
          <AlertCircle size={15} />
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">
          <div className="spinnerDot" />
          データを取得中...
        </div>
      ) : null}

      <div className="dashboardGrid">
        <EquityCurve reports={data.reports} />
        <ModeComparison reports={data.reports} />
        <StrategyComparison reports={data.reports} />
        <CandidateList candidates={data.candidates} />
        <TradeTable trades={data.trades} />
        <StrategyParamsPanel experiments={data.experiments} />
        <OpenAICostPanel costs={costs} />
        <DataSourceComparisonPanel comparison={comparison} loading={running === "compare-data-sources"} onCompare={compareSources} />
        <LlmAnalystPanel report={data.llm_report} />
      </div>

      <footer className="footerNote">
        <BarChart3 size={13} />
        TenKToMillion — ペーパートレード専用。リアル市場データはシミュレーション検証にのみ使用します。
      </footer>
    </main>
  );
}

function Metric({ icon, label, value, tone }: { icon: ReactNode; label: string; value: string; tone?: "positive" | "negative" }) {
  return (
    <article className={`metricCard${tone ? ` ${tone}` : ""}`}>
      <span className="metricIcon">{icon}</span>
      <span className="metricLabel">{label}</span>
      <strong className={`metricValue${tone ? ` ${tone}` : ""}`}>{value}</strong>
    </article>
  );
}

function ActionButton({
  label,
  action,
  running,
  onRun,
}: {
  label: string;
  action: "run-screening" | "run-paper-trade" | "run-analysis" | "run-optimization";
  running: string | null;
  onRun: (action: "run-screening" | "run-paper-trade" | "run-analysis" | "run-optimization") => Promise<void>;
}) {
  return (
    <button className="btn-primary" disabled={running !== null} onClick={() => void onRun(action)} type="button">
      <Play size={13} />
      {running === action ? "実行中..." : label}
    </button>
  );
}

function LlmActionButton({
  label,
  action,
  running,
  onRun,
}: {
  label: string;
  action: "run-daily-analysis" | "backtest-proposals";
  running: string | null;
  onRun: (action: "run-daily-analysis" | "backtest-proposals") => Promise<void>;
}) {
  return (
    <button className="btn-ai" disabled={running !== null} onClick={() => void onRun(action)} type="button">
      <Bot size={13} />
      {running === action ? "実行中..." : label}
    </button>
  );
}
