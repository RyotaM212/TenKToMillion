import type { Report } from "../api";

export function ModeComparison({ reports }: { reports: Report[] }) {
  const modes = aggregate(reports, "mode");
  return (
    <section className="panel">
      <h2>モード別比較</h2>
      <div className="comparisonGrid">
        {modes.map((mode) => (
          <div className="comparisonCard" key={mode.name}>
            <div className="name">{mode.name}</div>
            <div className={`value ${mode.pnl >= 0 ? "positive" : "negative"}`}>
              {mode.pnl >= 0 ? "+" : ""}
              {mode.pnl.toLocaleString()}円
            </div>
            <div className="sub">{mode.trades} trades</div>
          </div>
        ))}
        {modes.length === 0 && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>まだレポートがありません。</p>}
      </div>
    </section>
  );
}

function aggregate<T extends "mode" | "strategy_name">(reports: Report[], key: T) {
  const map = new Map<string, { name: string; pnl: number; trades: number }>();
  for (const report of reports) {
    const name = report[key];
    const item = map.get(name) ?? { name, pnl: 0, trades: 0 };
    item.pnl += report.daily_pnl;
    item.trades += 1;
    map.set(name, item);
  }
  return [...map.values()].sort((a, b) => b.pnl - a.pnl);
}
