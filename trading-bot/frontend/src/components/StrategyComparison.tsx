import type { Report } from "../api";

export function StrategyComparison({ reports }: { reports: Report[] }) {
  const strategies = aggregate(reports);
  return (
    <section className="panel">
      <h2>戦略別比較</h2>
      <div className="comparisonGrid">
        {strategies.map((s) => (
          <div className="comparisonCard" key={s.name}>
            <div className="name">{s.name}</div>
            <div className={`value ${s.pnl >= 0 ? "positive" : "negative"}`}>
              {s.pnl >= 0 ? "+" : ""}
              {s.pnl.toLocaleString()}円
            </div>
            <div className="sub">勝率 {(s.winRate * 100).toFixed(1)}%</div>
          </div>
        ))}
        {strategies.length === 0 && <div className="emptyState">まだレポートがありません</div>}
      </div>
    </section>
  );
}

function aggregate(reports: Report[]) {
  const map = new Map<string, { name: string; pnl: number; winRate: number }>();
  for (const report of reports) {
    const item = map.get(report.strategy_name) ?? { name: report.strategy_name, pnl: 0, winRate: 0 };
    item.pnl += report.daily_pnl;
    item.winRate = Math.max(item.winRate, report.win_rate);
    map.set(report.strategy_name, item);
  }
  return [...map.values()].sort((a, b) => b.pnl - a.pnl);
}
