import { ReceiptText } from "lucide-react";
import type { LlmCostHistory } from "../api";

export function OpenAICostPanel({ costs }: { costs: LlmCostHistory | null }) {
  const items = costs?.items ?? [];
  return (
    <section className="panel costPanel">
      <div className="panelHeader">
        <div>
          <h2>OpenAI Cost</h2>
          <p className="muted">保存済みtoken usageからの概算です。OpenAIへの追加リクエストは行いません。</p>
        </div>
        <ReceiptText size={17} />
      </div>

      <div className="costSummary">
        <div>
          <span>累計概算</span>
          <strong>¥{(costs?.total_estimated_cost_jpy ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</strong>
        </div>
        <div>
          <span>USD</span>
          <strong>${(costs?.total_estimated_cost_usd ?? 0).toFixed(4)}</strong>
        </div>
        <div>
          <span>Tokens</span>
          <strong>{(costs?.total_tokens ?? 0).toLocaleString()}</strong>
        </div>
      </div>

      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>日時</th>
              <th>MODEL</th>
              <th>STATUS</th>
              <th>TOKENS</th>
              <th>CACHED</th>
              <th>JPY</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{formatDateTime(item.started_at)}</td>
                <td>{item.model_name}</td>
                <td>
                  <span className={`miniStatus ${item.status}`}>{item.status}</span>
                </td>
                <td>{item.total_tokens.toLocaleString()}</td>
                <td>{item.cached_prompt_tokens.toLocaleString()}</td>
                <td>¥{item.estimated_cost_jpy.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
              </tr>
            ))}
            {items.length === 0 ? (
              <tr>
                <td colSpan={6}>OpenAI APIの実行履歴がありません。</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
      <p className="muted">{costs?.currency_note ?? "概算表示です。"}</p>
    </section>
  );
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("ja-JP", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
