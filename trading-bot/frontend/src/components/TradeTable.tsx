import type { Trade } from "../api";

export function TradeTable({ trades }: { trades: Trade[] }) {
  return (
    <section className="panel">
      <h2>取引履歴</h2>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>Mode</th>
              <th>Strategy</th>
              <th>銘柄</th>
              <th>数量</th>
              <th>損益</th>
              <th>理由</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => (
              <tr key={trade.id}>
                <td style={{ color: "var(--text-muted)", fontSize: 11, fontWeight: 600, letterSpacing: "0.04em" }}>{trade.mode}</td>
                <td>
                  <span className="strategyTag">{trade.strategy_name}</span>
                </td>
                <td style={{ fontWeight: 600 }}>{trade.symbol_name}</td>
                <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>{trade.quantity}</td>
                <td className={`pnlCell ${trade.pnl >= 0 ? "positive" : "negative"}`}>
                  {trade.pnl >= 0 ? "+" : ""}
                  {trade.pnl.toLocaleString()}円
                </td>
                <td style={{ color: "var(--text-muted)", fontSize: 12 }}>{trade.exit_reason}</td>
              </tr>
            ))}
            {trades.length === 0 && (
              <tr>
                <td colSpan={6} style={{ color: "var(--text-muted)", textAlign: "center", padding: "24px" }}>
                  取引履歴がありません。
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
