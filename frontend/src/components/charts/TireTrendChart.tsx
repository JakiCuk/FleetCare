import {
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useTranslation } from 'react-i18next';
import type { TireTrend } from '@/types';
import { formatKmCompact } from '@/lib/format';

interface TireTrendChartProps {
  trend: TireTrend;
  height?: number;
}

/**
 * Tread trend: solid "actual" + dashed "projected" lines, with a red
 * ReferenceLine at y=1.6 mm (DESIGN_SYSTEM §6).
 */
export function TireTrendChart({ trend, height = 240 }: TireTrendChartProps) {
  const { t } = useTranslation();

  // Merge actual + projection on the km axis so both series render on one chart.
  const byKm = new Map<number, { km: number; actual?: number; projected?: number }>();
  for (const p of trend.points) {
    byKm.set(p.km, { km: p.km, actual: p.actual });
  }
  for (const p of trend.projection) {
    const existing = byKm.get(p.km) ?? { km: p.km };
    existing.projected = p.projected;
    byKm.set(p.km, existing);
  }
  // Bridge the gap: the last actual point seeds the projected line.
  const lastActual = trend.points[trend.points.length - 1];
  if (lastActual && trend.projection.length > 0) {
    const entry = byKm.get(lastActual.km);
    if (entry && entry.projected === undefined) entry.projected = lastActual.actual;
  }

  const data = [...byKm.values()].sort((a, b) => a.km - b.km);
  const reference = trend.reference_mm ?? 1.6;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey="km"
          type="number"
          domain={['dataMin', 'dataMax']}
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
          tickFormatter={(v: number) => formatKmCompact(v)}
        />
        <YAxis
          domain={[0, 10]}
          ticks={[0, 2, 4, 6, 8, 10]}
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={false}
          width={32}
          unit=""
        />
        <Tooltip
          formatter={(value: number, name: string) => [`${value.toFixed(1)} mm`, name]}
          labelFormatter={(km: number) => `${km.toLocaleString()} km`}
          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
        />
        <ReferenceLine
          y={reference}
          stroke="#dc2626"
          strokeDasharray="5 4"
          label={{
            value: t('tires.minLabel'),
            position: 'insideTopRight',
            fontSize: 10,
            fill: '#dc2626',
          }}
        />
        <Line
          type="monotone"
          dataKey="actual"
          name={t('tires.trendTitle')}
          stroke="#2563eb"
          strokeWidth={2}
          dot={{ r: 3, fill: '#2563eb' }}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="projected"
          name={t('tires.prediction')}
          stroke="#94a3b8"
          strokeWidth={2}
          strokeDasharray="6 5"
          dot={false}
          connectNulls
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export default TireTrendChart;
