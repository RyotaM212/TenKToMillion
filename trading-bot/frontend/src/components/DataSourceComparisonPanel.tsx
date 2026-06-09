import { Database, GitCompareArrows } from "lucide-react";
import type { DataSourceComparison, DataSourceResult } from "../api";

export function DataSourceComparisonPanel({
  comparison,
  loading,
  onCompare,
}: {
  comparison: DataSourceComparison | null;
  loading: boolean;
  onCompare: () => Promise<void>;
}) {
  const sources = comparison ? Object.values(comparison.sources) : [];
  return (
    <section className="panel dataSourcePanel">
      <div className="panelHeader">
        <div>
          <h2>Data Source Compare</h2>
          <p className="muted">J-QuantsとYahoo系を同じスコアリングで比較します。実行時のみ外部データを取得します。</p>
        </div>
        <button className="iconTextButton" type="button" disabled={loading} onClick={() => void onCompare()}>
          <GitCompareArrows size={14} />
          {loading ? "比較中..." : "比較"}
        </button>
      </div>

      {comparison ? <p className="comparisonSummary">{comparison.summary}</p> : <p className="muted">比較ボタンで二系統の候補差分を確認できます。</p>}

      {comparison?.overlap_symbols.length ? (
        <div className="overlapLine">
          <Database size={13} />
          共通候補: {comparison.overlap_symbols.join(", ")}
        </div>
      ) : null}

      <div className="sourceCompareGrid">
        {sources.map((source) => (
          <SourceColumn key={source.source} source={source} />
        ))}
      </div>
    </section>
  );
}

function SourceColumn({ source }: { source: DataSourceResult }) {
  return (
    <article className="sourceColumn">
      <div className="sourceColumnHead">
        <strong>{source.source}</strong>
        <span className={`miniStatus ${source.status}`}>{source.status}</span>
      </div>
      <p className="muted">
        snapshots {source.snapshot_count} / candidates {source.candidate_count}
      </p>
      {source.error_message ? <p className="sourceError">{source.error_message}</p> : null}
      <ol>
        {source.top_candidates.slice(0, 5).map((candidate) => (
          <li key={`${source.source}-${candidate.symbol}-${candidate.strategy_name}`}>
            <span>
              {candidate.symbol} {candidate.symbol_name}
            </span>
            <strong>{candidate.score.toFixed(1)}</strong>
          </li>
        ))}
      </ol>
    </article>
  );
}
