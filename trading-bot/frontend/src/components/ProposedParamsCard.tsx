export function ProposedParamsCard({ params, backtestResult, adopted }: { params: Record<string, unknown>; backtestResult: Record<string, unknown>; adopted: boolean }) {
  return (
    <section className="proposedParams">
      <div>
        <h3>提案パラメータ</h3>
        <dl>
          {Object.entries(params).map(([key, value]) => (
            <div key={key}>
              <dt>{key}</dt>
              <dd>{String(value)}</dd>
            </div>
          ))}
        </dl>
      </div>
      <div>
        <h3>バックテスト結果</h3>
        <dl>
          {Object.entries(backtestResult).map(([key, value]) => (
            <div key={key}>
              <dt>{key}</dt>
              <dd>{String(value)}</dd>
            </div>
          ))}
        </dl>
        <span className={adopted ? "badge adopted" : "badge"}>{adopted ? "採用候補" : "要確認"}</span>
      </div>
    </section>
  );
}
