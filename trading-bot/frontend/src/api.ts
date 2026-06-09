export type Candidate = {
  id: number;
  symbol: string;
  symbol_name: string;
  score: number;
  strategy_name: string;
  selected_reason: string;
};

export type Trade = {
  id: number;
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
};

export type Experiment = {
  id: number;
  strategy_name: string;
  proposed_params_json: string;
  backtest_result_json: string;
  adopted: number;
  reason: string;
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
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
