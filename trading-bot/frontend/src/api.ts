export type Candidate = {
  id: number;
  trade_date: string;
  symbol: string;
  symbol_name: string;
  score: number;
  strategy_name: string;
  selected_reason: string;
  created_at?: string;
};

export type Trade = {
  id: number;
  trade_date: string;
  mode: string;
  strategy_name: string;
  symbol: string;
  symbol_name: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_rate: number;
  exit_reason: string;
  created_at?: string;
};

export type Report = {
  id: number;
  trade_date: string;
  mode: string;
  strategy_name: string;
  end_cash: number;
  daily_pnl: number;
  win_rate: number;
  max_drawdown: number;
  created_at?: string;
};

export type Experiment = {
  id: number;
  experiment_date?: string;
  strategy_name: string;
  proposed_params_json: string;
  backtest_result_json: string;
  adopted: number;
  reason: string;
  created_at?: string;
};

export type LlmAnalysisReport = {
  id: number;
  analysis_date: string;
  model_name: string;
  summary_text: string;
  win_patterns: string;
  lose_patterns: string;
  risk_notes: string;
  improvement_suggestions: string;
  next_day_hypotheses: string;
  proposed_params_json: string;
  confidence_score: number;
  backtest_result_json: string;
  adopted: number;
  created_at?: string;
};

export type LlmCostItem = {
  id: number;
  analysis_date: string;
  status: string;
  model_name: string;
  started_at: string;
  finished_at: string | null;
  prompt_tokens: number;
  cached_prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  estimated_cost_jpy: number;
  error_message: string | null;
};

export type LlmCostHistory = {
  items: LlmCostItem[];
  total_estimated_cost_usd: number;
  total_estimated_cost_jpy: number;
  total_tokens: number;
  currency_note: string;
};

export type SourceCandidate = {
  symbol: string;
  symbol_name: string;
  strategy_name: string;
  score: number;
  selected_reason: string;
};

export type DataSourceResult = {
  source: string;
  status: string;
  snapshot_count: number;
  candidate_count: number;
  top_candidates: SourceCandidate[];
  error_message: string | null;
};

export type DataSourceComparison = {
  sources: Record<string, DataSourceResult>;
  overlap_symbols: string[];
  summary: string;
};

export type DashboardData = {
  current_asset: number;
  buying_power: number;
  locked_profit: number;
  today_pnl: number;
  total_pnl: number;
  win_rate: number;
  max_drawdown: number;
  mode: string;
  active_strategy: string;
  data_source: string;
  candidates: Candidate[];
  positions: unknown[];
  trades: Trade[];
  reports: Report[];
  experiments: Experiment[];
  llm_report: LlmAnalysisReport | null;
};

export type HealthStatus = {
  ok: boolean;
  scheduler_enabled: boolean;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/api/health`);
  if (!response.ok) {
    throw new Error("Health API の取得に失敗しました");
  }
  return response.json();
}

export async function fetchDashboard(): Promise<DashboardData> {
  const response = await fetch(`${API_BASE}/api/dashboard`);
  if (!response.ok) {
    throw new Error("Dashboard API の取得に失敗しました");
  }
  return response.json();
}

export async function postBotAction(action: "run-screening" | "run-paper-trade" | "run-analysis" | "run-optimization") {
  const response = await fetch(`${API_BASE}/api/bot/${action}`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`${action} の実行に失敗しました`);
  }
  return response.json();
}

export async function postLlmAction(action: "run-daily-analysis" | "backtest-proposals") {
  const response = await fetch(`${API_BASE}/api/llm/${action}`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`${action} の実行に失敗しました`);
  }
  return response.json();
}

export async function fetchLlmCosts(): Promise<LlmCostHistory> {
  const response = await fetch(`${API_BASE}/api/llm/costs`);
  if (!response.ok) {
    throw new Error("OpenAI料金履歴の取得に失敗しました");
  }
  return response.json();
}

export async function fetchDataSourceComparison(): Promise<DataSourceComparison> {
  const response = await fetch(`${API_BASE}/api/data-sources/compare`);
  if (!response.ok) {
    throw new Error("データソース比較の取得に失敗しました");
  }
  return response.json();
}

export async function postState(endpoint: "set-mode" | "set-data-source" | "set-strategy", value: string) {
  const response = await fetch(`${API_BASE}/api/bot/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
  });
  if (!response.ok) {
    throw new Error(`${endpoint} の更新に失敗しました`);
  }
  return response.json();
}
