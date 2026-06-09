import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Report } from "../api";

export function EquityCurve({ reports }: { reports: Report[] }) {
  const data = [...reports].reverse().map((report, index) => ({
    name: `${report.trade_date}-${index + 1}`,
    equity: report.end_cash,
  }));

  return (
    <section className="panel">
      <h2>資産推移</h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="name" hide />
            <YAxis width={58} />
            <Tooltip />
            <Line type="monotone" dataKey="equity" stroke="#116466" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
