import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { OdometerReading } from '@/types';
import { formatKmCompact, formatDate } from '@/lib/format';

interface OdometerChartProps {
  readings: OdometerReading[];
  height?: number;
}

/** Line + area gradient of odometer over time (DESIGN_SYSTEM §6). */
export function OdometerChart({ readings, height = 220 }: OdometerChartProps) {
  const data = [...readings]
    .sort((a, b) => +new Date(a.recorded_at) - +new Date(b.recorded_at))
    .map((r) => ({
      date: formatDate(r.recorded_at),
      km: r.reading_km,
    }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="odoGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563eb" stopOpacity={0.25} />
            <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => formatKmCompact(v)}
          width={48}
          domain={['dataMin', 'dataMax']}
        />
        <Tooltip
          formatter={(value: number) => [`${value.toLocaleString()} km`, 'km']}
          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
        />
        <Area
          type="monotone"
          dataKey="km"
          stroke="#2563eb"
          strokeWidth={2}
          fill="url(#odoGradient)"
          dot={{ r: 3, fill: '#2563eb' }}
          activeDot={{ r: 5 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export default OdometerChart;
