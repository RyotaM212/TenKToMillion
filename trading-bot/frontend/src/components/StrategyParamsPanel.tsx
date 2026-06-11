import type { Experiment } from "../api";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const PAGE_SIZE = 5;

export function StrategyParamsPanel({ experiments }: { experiments: Experiment[] }) {
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(experiments.length / PAGE_SIZE));
  const visibleExperiments = useMemo(() => {
    const start = page * PAGE_SIZE;
    return experiments.slice(start, start + PAGE_SIZE);
  }, [experiments, page]);

  useEffect(() => {
    setPage((current) => Math.min(current, pageCount - 1));
  }, [pageCount]);

  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <h2>改善提案</h2>
          <p className="muted">
            {experiments.length > 0 ? `${experiments.length}件中 ${page * PAGE_SIZE + 1}-${Math.min((page + 1) * PAGE_SIZE, experiments.length)}件を表示` : "まだ改善提案がありません"}
          </p>
        </div>
        <div className="pagerControls" aria-label="改善提案ページング">
          <button className="iconButton compact" type="button" disabled={page === 0} onClick={() => setPage((current) => Math.max(current - 1, 0))} title="前の改善提案">
            <ChevronLeft size={14} />
          </button>
          <span>
            {page + 1}/{pageCount}
          </span>
          <button
            className="iconButton compact"
            type="button"
            disabled={page >= pageCount - 1}
            onClick={() => setPage((current) => Math.min(current + 1, pageCount - 1))}
            title="次の改善提案"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
      <div className="experimentList">
        {visibleExperiments.map((experiment) => (
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
