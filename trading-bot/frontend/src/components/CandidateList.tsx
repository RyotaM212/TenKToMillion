import type { Candidate } from "../api";

export function CandidateList({ candidates }: { candidates: Candidate[] }) {
  return (
    <section className="panel">
      <h2>本日の候補 TOP20</h2>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>銘柄</th>
              <th>名称</th>
              <th>戦略</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c) => (
              <tr key={c.id}>
                <td style={{ fontFamily: "var(--mono, 'JetBrains Mono', monospace)", fontWeight: 600 }}>{c.symbol}</td>
                <td style={{ color: "var(--text-secondary)" }}>{c.symbol_name}</td>
                <td>
                  <span className="strategyTag">{c.strategy_name}</span>
                </td>
                <td>
                  <div className="scoreBar">
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, minWidth: 28 }}>{c.score.toFixed(1)}</span>
                    <div className="scoreBarTrack">
                      <div className="scoreBarFill" style={{ width: `${Math.min(c.score * 10, 100)}%` }} />
                    </div>
                  </div>
                </td>
              </tr>
            ))}
            {candidates.length === 0 && (
              <tr>
                <td colSpan={4} style={{ color: "var(--text-muted)", textAlign: "center", padding: "24px" }}>
                  候補がありません。候補生成を実行してください。
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
