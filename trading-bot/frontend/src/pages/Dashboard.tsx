import { Activity, BarChart3, Bot, Database, Play, RefreshCw, ShieldCheck, Wallet } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import type { DashboardData } from "../api";
import { fetchDashboard, postBotAction, postState } from "../api";
import { CandidateList } from "../components/CandidateList";
import { EquityCurve } from "../components/EquityCurve";
import { ModeComparison } from "../components/ModeComparison";
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
  data_source: "mock",
  candidates: [],
  positions: [],
  trades: [],
  reports: [],
  experiments: [],
};

export function Dashboard() {
  const [data, setData] = useState<DashboardData>(emptyDashboard);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      setData(await fetchDashboard());
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

  useEffect(() => {
    void load();
  }, []);

  return (
    <main className="appShell">
      <header className="topbar">
        <div>
          <h1>TenKToMillion</h1>
          <p>Paper trading only. 現物・空売りなし・レバレッジなし。</p>
        </div>
        <button className="iconButton" onClick={() => void load()} title="更新" type="button">
          <RefreshCw size={18} />
        </button>
      </header>

      <section className="statusStrip">
        <Metric icon={<Wallet />} label="現在資産" value={`${data.current_asset.toLocaleString()}円`} />
        <Metric icon={<Activity />} label="本日の損益" value={`${data.today_pnl.toLocaleString()}円`} tone={data.today_pnl >= 0 ? "positive" : "negative"} />
        <Metric icon={<ShieldCheck />} label="ロック済み利益" value={`${data.locked_profit.toLocaleString()}円`} />
        <Metric icon={<Database />} label="データソース" value={data.data_source} />
        <Metric icon={<Bot />} label="現在モード" value={data.mode} />
        <Metric icon={<BarChart3 />} label="表示戦略" value={data.active_strategy} />
      </section>

      <section className="actionBar">
        <ActionButton label="候補生成" action="run-screening" running={running} onRun={run} />
        <ActionButton label="ペーパー実行" action="run-paper-trade" running={running} onRun={run} />
        <ActionButton label="日次分析" action="run-analysis" running={running} onRun={run} />
        <ActionButton label="改善案生成" action="run-optimization" running={running} onRun={run} />
      </section>

      <section className="settingsBar">
        <label>
          データソース
          <select
            disabled={running !== null}
            value={data.data_source}
            onChange={(event) => void updateState("set-data-source", event.currentTarget.value)}
          >
            <option value="mock">Mock</option>
            <option value="yahoo">Yahoo系</option>
            <option value="jquants">J-Quants</option>
          </select>
        </label>
        <label>
          資金管理
          <select disabled={running !== null} value={data.mode} onChange={(event) => void updateState("set-mode", event.currentTarget.value)}>
            <option value="YOLO_MODE">YOLO_MODE</option>
            <option value="LOCK_PROFIT_MODE">LOCK_PROFIT_MODE</option>
            <option value="ONE_SHOT_MODE">ONE_SHOT_MODE</option>
          </select>
        </label>
        <label>
          表示戦略
          <select disabled={running !== null} value={data.active_strategy} onChange={(event) => void updateState("set-strategy", event.currentTarget.value)}>
            <option value="VolumeStrategy">VolumeStrategy</option>
            <option value="MomentumStrategy">MomentumStrategy</option>
            <option value="NewsStrategy">NewsStrategy</option>
            <option value="HybridStrategy">HybridStrategy</option>
          </select>
        </label>
      </section>

      {error && <div className="errorBox">{error}</div>}
      {loading ? <div className="loading">Loading...</div> : null}

      <div className="dashboardGrid">
        <EquityCurve reports={data.reports} />
        <ModeComparison reports={data.reports} />
        <StrategyComparison reports={data.reports} />
        <CandidateList candidates={data.candidates} />
        <TradeTable trades={data.trades} />
        <StrategyParamsPanel experiments={data.experiments} />
      </div>

      <footer className="footerNote">
        <BarChart3 size={16} />
        実注文は無効化されています。リアル市場データはペーパートレード検証にのみ使用します。
      </footer>
    </main>
  );
}

function Metric({ icon, label, value, tone }: { icon: ReactNode; label: string; value: string; tone?: "positive" | "negative" }) {
  return (
    <article className="metricCard">
      <span className="metricIcon">{icon}</span>
      <span>{label}</span>
      <strong className={tone}>{value}</strong>
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
    <button disabled={running !== null} onClick={() => void onRun(action)} type="button">
      <Play size={16} />
      {running === action ? "実行中" : label}
    </button>
  );
}
