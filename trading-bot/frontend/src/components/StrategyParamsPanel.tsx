import type { Experiment } from "../api";

export function StrategyParamsPanel({ experiments }: { experiments: Experiment[] }) {
  return (
    <section className="panel">
      <h2>改善提案</h2>
      <div className="experimentList">
        {experiments.map((experiment) => (
          <article key={experiment.id} className="experimentItem">
            <div>
              <strong>{experiment.strategy_name}</strong>
              <p>{experiment.reason}</p>
            </div>
            <span className={experiment.adopted ? "badge adopted" : "badge"}>{experiment.adopted ? "採用候補" : "保留"}</span>
          </article>
        ))}
        {experiments.length === 0 && <div className="emptyState">まだ改善提案がありません</div>}
      </div>
    </section>
  );
}
