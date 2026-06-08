import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import type { ExpenseBreakdownItem } from '@/types';
import { expenseCategoryHex } from '@/lib/colors';
import { formatMoney } from '@/lib/format';

interface CostPieChartProps {
  data: ExpenseBreakdownItem[];
  currency?: string;
  height?: number;
}

/** Donut chart of expense categories (DESIGN_SYSTEM §6). */
export function CostPieChart({ data, currency = 'EUR', height = 200 }: CostPieChartProps) {
  const chartData = data.filter((d) => d.amount > 0);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="amount"
          nameKey="category"
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={80}
          paddingAngle={2}
          stroke="none"
        >
          {chartData.map((entry) => (
            <Cell
              key={entry.category}
              fill={expenseCategoryHex[entry.category] ?? expenseCategoryHex.other}
            />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => formatMoney(value, currency)}
          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export default CostPieChart;
