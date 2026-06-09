import type { Report } from "../api";

export function ModeComparison({ reports }: { reports: Report[] }) {
  const modes = aggregate(reports, "mode");
  return (
    <section className="panel">
      <h2>モード別比較</h2>
      <div className="comparisonGrid">
        {modes.map((mode) => (
          <div className="metricCard" key={mode.name}>
            <span>{mode.name}</span>
            <strong className={mode.pnl >= 0 ? "positive" : "negative"}>{mode.pnl.toLocaleString()}円</strong>
            <small>{mode.trades} trades</small>
          </div>
        ))}
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
