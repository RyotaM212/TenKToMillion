import { Bot } from "lucide-react";
import type { LlmAnalysisReport } from "../api";
import { LlmSuggestionList } from "./LlmSuggestionList";
import { ProposedParamsCard } from "./ProposedParamsCard";

export function LlmAnalystPanel({ report }: { report: LlmAnalysisReport | null }) {
  if (!report) {
    return (
      <section className="panel llmPanel">
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <Bot size={14} style={{ color: "var(--ai)" }} />
          <h2 style={{ color: "var(--ai)" }}>AI Analyst</h2>
        </div>
        <p className="muted">まだAI分析レポートはありません。「AI分析実行」を押してください。</p>
      </section>
    );
  }

  const winPatterns = parseStringList(report.win_patterns);
  const losePatterns = parseStringList(report.lose_patterns);
  const riskNotes = parseStringList(report.risk_notes);
  const improvements = parseStringList(report.improvement_suggestions);
  const hypotheses = parseStringList(report.next_day_hypotheses);
  const proposedParams = parseObject(report.proposed_params_json);
  const backtestResult = parseObject(report.backtest_result_json);

  return (
    <section className="panel llmPanel">
      <div className="panelHeader">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <Bot size={14} style={{ color: "var(--ai)" }} />
            <h2 style={{ color: "var(--ai)" }}>AI Analyst</h2>
          </div>
          <p className="muted">
            {report.analysis_date} &nbsp;·&nbsp; {report.model_name}
          </p>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="confidence">{Math.round(report.confidence_score * 100)}%</div>
          <p className="muted" style={{ marginTop: 2 }}>信頼度</p>
        </div>
      </div>
      <p className="llmSummary">{report.summary_text}</p>
      <div className="llmGrid">
        <LlmSuggestionList title="勝ちパターン" items={winPatterns} />
        <LlmSuggestionList title="負けパターン" items={losePatterns} />
        <LlmSuggestionList title="危険な傾向" items={riskNotes} />
        <LlmSuggestionList title="改善提案" items={improvements} />
        <LlmSuggestionList title="翌日仮説" items={hypotheses} />
      </div>
      <ProposedParamsCard params={proposedParams} backtestResult={backtestResult} adopted={report.adopted === 1} />
    </section>
  );
}

function parseStringList(value: string): string[] {
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}

function parseObject(value: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}
