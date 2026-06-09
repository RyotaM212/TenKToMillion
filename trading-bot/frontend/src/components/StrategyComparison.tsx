import type { Report } from "../api";

export function StrategyComparison({ reports }: { reports: Report[] }) {
  const strategies = aggregate(reports);
  return (
    <section className="panel">
      <h2>戦略AI別比較</h2>
      <div className="comparisonGrid">
        {strategies.map((strategy) => (
          <div className="metricCard" key={strategy.name}>
            <span>{strategy.name}</span>
            <strong className={strategy.pnl >= 0 ? "positive" : "negative"}>{strategy.pnl.toLocaleString()}円</strong>
            <small>勝率 {(strategy.winRate * 100).toFixed(1)}%</small>
          </div>
        ))}
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
