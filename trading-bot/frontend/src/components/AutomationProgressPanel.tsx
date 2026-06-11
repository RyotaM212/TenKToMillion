import { Activity, Bot, CheckCircle2, Clock3, Search, ShieldCheck, Sparkles, TimerReset } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { DashboardData, HealthStatus } from "../api";

type Phase = {
  id: string;
  time: string;
  label: string;
  detail: string;
  icon: typeof Search;
  done: (data: DashboardData) => boolean;
  lastAt: (data: DashboardData) => string | undefined;
};

const PHASES: Phase[] = [
  {
    id: "screening",
    time: "08:30",
    label: "候補生成",
    detail: "市場データから候補銘柄を抽出",
    icon: Search,
    done: (data) => data.candidates.length > 0,
    lastAt: (data) => latestTimestamp(data.candidates),
  },
  {
    id: "paper_trade",
    time: "09:10",
    label: "ペーパー実行",
    detail: "条件一致時だけ仮想エントリー",
    icon: Activity,
    done: (data) => data.trades.length > 0,
    lastAt: (data) => latestTimestamp(data.trades),
  },
  {
    id: "stop_entries",
    time: "10:30",
    label: "新規停止",
    detail: "新しいエントリーを止める時間帯",
    icon: ShieldCheck,
    done: () => minutesNowJst() >= timeToMinutes("10:30"),
    lastAt: () => undefined,
  },
  {
    id: "force_exit",
    time: "14:45",
    label: "強制決済",
    detail: "仮想ポジションを日中で閉じる",
    icon: TimerReset,
    done: () => minutesNowJst() >= timeToMinutes("14:45"),
    lastAt: () => undefined,
  },
  {
    id: "daily_analysis",
    time: "15:30",
    label: "日次分析",
    detail: "損益と戦略別の結果を集計",
    icon: CheckCircle2,
    done: (data) => data.reports.length > 0,
    lastAt: (data) => latestTimestamp(data.reports),
  },
  {
    id: "llm_analysis",
    time: "15:45",
    label: "AI分析",
    detail: "OpenAIで改善点を整理",
    icon: Bot,
    done: (data) => Boolean(data.llm_report),
    lastAt: (data) => data.llm_report?.created_at,
  },
  {
    id: "optimization",
    time: "16:15",
    label: "改善案",
    detail: "採用候補パラメータを検証",
    icon: Sparkles,
    done: (data) => data.experiments.length > 0,
    lastAt: (data) => latestTimestamp(data.experiments),
  },
];

export function AutomationProgressPanel({ data, health, running }: { data: DashboardData; health: HealthStatus | null; running: string | null }) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  const status = useMemo(() => buildProgressStatus(data, health, running, now), [data, health, running, now]);
  const progressPercent = Math.round((status.completedCount / PHASES.length) * 100);

  return (
    <section className="automationProgress">
      <div className="progressOverview">
        <div>
          <p className="eyebrow">AUTO RUN PHASE</p>
          <h2>{status.current.label}</h2>
          <p>{status.current.description}</p>
        </div>
        <div className="nextRunBox">
          <Clock3 size={15} />
          <div>
            <span>次の予定</span>
            <strong>
              {status.next ? `${status.next.time} ${status.next.label}` : "本日の自動予定は完了"}
            </strong>
          </div>
        </div>
      </div>

      <div className="progressMeter" aria-label={`自動運転進捗 ${progressPercent}%`}>
        <span style={{ width: `${progressPercent}%` }} />
      </div>

      <div className="phaseRail">
        {PHASES.map((phase) => {
          const phaseStatus = status.phaseStatuses[phase.id];
          const Icon = phase.icon;
          return (
            <article key={phase.id} className={`phaseStep ${phaseStatus}`}>
              <span className="phaseIcon">
                <Icon size={15} />
              </span>
              <div>
                <strong>{phase.label}</strong>
                <span>{phase.time}</span>
                <p>{phaseStatus === "done" ? formatLastAt(phase.lastAt(data)) : phase.detail}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function buildProgressStatus(data: DashboardData, health: HealthStatus | null, running: string | null, now: Date) {
  const nowMinutes = minutesJst(now);
  const next = PHASES.find((phase) => timeToMinutes(phase.time) > nowMinutes);
  const active = [...PHASES].reverse().find((phase) => timeToMinutes(phase.time) <= nowMinutes) ?? PHASES[0];
  const phaseStatuses = Object.fromEntries(
    PHASES.map((phase) => {
      if (running && actionMatchesPhase(running, phase.id)) {
        return [phase.id, "active"];
      }
      if (phase.done(data)) {
        return [phase.id, "done"];
      }
      if (phase.id === active.id && health?.ok) {
        return [phase.id, "active"];
      }
      return [phase.id, "waiting"];
    }),
  );
  const completedCount = Object.values(phaseStatuses).filter((value) => value === "done").length;
  return {
    current: {
      label: running ? "手動実行中" : health?.ok ? active.label : "接続確認中",
      description: running ? runningLabel(running) : health?.ok ? active.detail : "backendのhealth checkを待っています。",
    },
    next,
    phaseStatuses,
    completedCount,
  };
}

function actionMatchesPhase(action: string, phaseId: string) {
  return (
    (action === "run-screening" && phaseId === "screening") ||
    (action === "run-paper-trade" && phaseId === "paper_trade") ||
    (action === "run-analysis" && phaseId === "daily_analysis") ||
    (action === "run-optimization" && phaseId === "optimization") ||
    (action === "run-daily-analysis" && phaseId === "llm_analysis") ||
    (action === "backtest-proposals" && phaseId === "optimization")
  );
}

function runningLabel(action: string) {
  const labels: Record<string, string> = {
    "run-screening": "候補生成を手動実行しています。",
    "run-paper-trade": "ペーパートレードを手動実行しています。",
    "run-analysis": "日次分析を手動実行しています。",
    "run-optimization": "改善案生成を手動実行しています。",
    "run-daily-analysis": "AI分析を手動実行しています。",
    "backtest-proposals": "AI提案の検証を手動実行しています。",
    "compare-data-sources": "J-QuantsとYahoo系を比較しています。",
  };
  return labels[action] ?? "処理を実行しています。";
}

function latestTimestamp(rows: Array<{ created_at?: string }>) {
  const timestamps = rows.map((row) => row.created_at).filter(Boolean).sort();
  return timestamps[timestamps.length - 1];
}

function formatLastAt(value: string | undefined) {
  if (!value) {
    return "完了済み";
  }
  const date = new Date(value.replace(" ", "T"));
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.toLocaleDateString("ja-JP", { month: "2-digit", day: "2-digit" })} ${date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" })}`;
}

function minutesNowJst() {
  return minutesJst(new Date());
}

function minutesJst(date: Date) {
  const parts = new Intl.DateTimeFormat("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Tokyo",
  }).formatToParts(date);
  const hour = Number(parts.find((part) => part.type === "hour")?.value ?? "0");
  const minute = Number(parts.find((part) => part.type === "minute")?.value ?? "0");
  return hour * 60 + minute;
}

function timeToMinutes(value: string) {
  const [hour, minute] = value.split(":").map(Number);
  return hour * 60 + minute;
}
