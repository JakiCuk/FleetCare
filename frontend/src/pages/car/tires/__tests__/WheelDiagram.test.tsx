import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { TireMeasurement } from '@/types';
import { WheelDiagram } from '@/pages/car/tires/WheelDiagram';

const measurement: TireMeasurement = {
  id: 1,
  measured_at: '2026-01-15',
  odometer_km: 127540,
  // Numbers from the API (no string coercion → no NaN).
  tread_fl_mm: 6.5,
  tread_fr_mm: 6.4,
  tread_rl_mm: 7.1,
  tread_rr_mm: 7.0,
  pressure_fl_after_bar: 2.3,
  pressure_fr_after_bar: 2.3,
  pressure_rl_after_bar: 2.2,
  pressure_rr_after_bar: 2.2,
};

describe('WheelDiagram', () => {
  it('renders numeric tread values and never shows NaN', () => {
    const { container } = render(<WheelDiagram measurement={measurement} />);
    expect(container.textContent).not.toContain('NaN');
    // sk-SK formats 6.5 as "6,5".
    expect(screen.getByText('6,5')).toBeInTheDocument();
    expect(screen.getByText('7,1')).toBeInTheDocument();
  });

  it('shows em dashes (not NaN) for a missing measurement', () => {
    const { container } = render(<WheelDiagram measurement={null} />);
    expect(container.textContent).not.toContain('NaN');
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(4);
  });
});
