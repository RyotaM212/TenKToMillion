import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Report } from "../api";

export function EquityCurve({ reports }: { reports: Report[] }) {
  const data = [...reports].reverse().map((report, index) => ({
    name: report.trade_date,
    equity: report.end_cash,
    index,
  }));

  const min = data.length ? Math.min(...data.map((d) => d.equity)) * 0.998 : 9000;
  const max = data.length ? Math.max(...data.map((d) => d.equity)) * 1.002 : 11000;

  return (
    <section className="panel">
      <h2>資産推移</h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
            <XAxis dataKey="name" hide />
            <YAxis
              width={70}
              domain={[min, max]}
              tickFormatter={(v: number) => `¥${(v / 1000).toFixed(0)}k`}
              tick={{ fill: "#6e7681", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "#1c2128",
                border: "1px solid #30363d",
                borderRadius: "8px",
                color: "#e6edf3",
                fontSize: "12px",
              }}
              formatter={(value: number) => [`¥${value.toLocaleString()}`, "資産"]}
              labelStyle={{ color: "#8b949e" }}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke="#22d3ee"
              strokeWidth={2}
              fill="url(#equityGradient)"
              dot={false}
              activeDot={{ r: 4, fill: "#22d3ee", strokeWidth: 0 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
