import { useTranslation } from 'react-i18next';
import { treadHex } from '@/lib/colors';
import { formatNumber } from '@/lib/format';
import type { TireMeasurement } from '@/types';

interface WheelDiagramProps {
  measurement: TireMeasurement | null;
}

function Wheel({ label, mm }: { label: string; mm: number | null | undefined }) {
  const color = treadHex(mm);
  return (
    <div
      className="rounded-lg px-4 py-2 text-center"
      style={{ background: `${color}18`, border: `1.5px solid ${color}40` }}
    >
      <div className="text-[10px] text-text-faint">{label}</div>
      <div className="text-[22px] font-bold leading-none" style={{ color }}>
        {mm === null || mm === undefined ? '—' : formatNumber(mm)}
      </div>
    </div>
  );
}

/** Top-down 4-wheel layout (FL/FR front, RL/RR rear) colored by tread mm (mockup :416–430). */
export function WheelDiagram({ measurement }: WheelDiagramProps) {
  const { t } = useTranslation();
  return (
    <div>
      <div className="mb-2 text-center text-[11px] text-text-faint">{t('tires.currentTread')}</div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-2">
        <Wheel label="FL" mm={measurement?.tread_fl_mm} />
        <Wheel label="FR" mm={measurement?.tread_fr_mm} />
        <Wheel label="RL" mm={measurement?.tread_rl_mm} />
        <Wheel label="RR" mm={measurement?.tread_rr_mm} />
      </div>
    </div>
  );
}

export default WheelDiagram;
