import { ReceiptText } from "lucide-react";
import type { LlmCostHistory } from "../api";

export function OpenAICostPanel({ costs }: { costs: LlmCostHistory | null }) {
  const items = costs?.items ?? [];

  return (
    <section className="panel costPanel">
      <div className="panelHeader">
        <div>
          <h2>
            <ReceiptText size={12} />
            OpenAI Cost
          </h2>
          <p className="muted">保存済みtoken usageからの概算。OpenAIへの追加リクエストは行いません。</p>
        </div>
      </div>

      <div className="costSummary">
        <div>
          <span>累計概算 JPY</span>
          <strong>¥{(costs?.total_estimated_cost_jpy ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</strong>
        </div>
        <div>
          <span>累計概算 USD</span>
          <strong>${(costs?.total_estimated_cost_usd ?? 0).toFixed(4)}</strong>
        </div>
        <div>
          <span>累計トークン</span>
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
                <td style={{ color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{formatDateTime(item.started_at)}</td>
                <td style={{ color: "var(--text-secondary)", fontSize: 12 }}>{item.model_name}</td>
                <td>
                  <span className={`miniStatus ${item.status}`}>{item.status}</span>
                </td>
                <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>{item.total_tokens.toLocaleString()}</td>
                <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "var(--text-muted)" }}>{item.cached_prompt_tokens.toLocaleString()}</td>
                <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "var(--warning)" }}>¥{item.estimated_cost_jpy.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={6}>
                  <div className="emptyState">OpenAI APIの実行履歴がありません</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="muted" style={{ marginTop: 10 }}>{costs?.currency_note ?? "概算表示です。"}</p>
    </section>
  );
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ja-JP", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}
