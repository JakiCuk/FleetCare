import { treadHex } from '@/lib/colors';
import { formatNumber } from '@/lib/format';
import type { TireMeasurement } from '@/types';

interface WheelDiagramProps {
  measurement: TireMeasurement | null;
}

function Wheel({ label, mm }: { label: string; mm: number | null | undefined }) {
  const color = treadHex(mm);
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="flex h-12 w-8 items-center justify-center rounded-md text-xs font-bold text-white"
        style={{ backgroundColor: color }}
        title={`${label}: ${formatNumber(mm)} mm`}
      >
        {mm === null || mm === undefined ? '—' : formatNumber(mm)}
      </div>
      <span className="text-[10px] font-medium text-text-muted">{label}</span>
    </div>
  );
}

/** Top-down 4-wheel layout (FL/FR front, RL/RR rear) colored by tread mm. */
export function WheelDiagram({ measurement }: WheelDiagramProps) {
  return (
    <div className="inline-grid grid-cols-2 gap-x-8 gap-y-4 rounded-lg border border-border-soft bg-bg/40 px-6 py-4">
      <Wheel label="FL" mm={measurement?.tread_fl_mm} />
      <Wheel label="FR" mm={measurement?.tread_fr_mm} />
      <Wheel label="RL" mm={measurement?.tread_rl_mm} />
      <Wheel label="RR" mm={measurement?.tread_rr_mm} />
    </div>
  );
}

export default WheelDiagram;
