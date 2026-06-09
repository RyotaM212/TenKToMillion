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
                <td>{trade.mode}</td>
                <td>{trade.strategy_name}</td>
                <td>{trade.symbol_name}</td>
                <td>{trade.quantity}</td>
                <td className={trade.pnl >= 0 ? "positive" : "negative"}>{trade.pnl.toLocaleString()}円</td>
                <td>{trade.exit_reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
