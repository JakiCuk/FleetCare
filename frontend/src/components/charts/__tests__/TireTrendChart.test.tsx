import { beforeAll, describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import type { TireTrend } from '@/types';
import { TireTrendChart } from '@/components/charts/TireTrendChart';

// Recharts' ResponsiveContainer relies on ResizeObserver, which jsdom lacks.
// Provide a minimal stub that reports a fixed, non-zero size so the chart can
// lay out and render its children without throwing.
beforeAll(() => {
  class ResizeObserverStub {
    callback: ResizeObserverCallback;
    constructor(callback: ResizeObserverCallback) {
      this.callback = callback;
    }
    observe() {
      this.callback(
        [{ contentRect: { width: 600, height: 240 } } as ResizeObserverEntry],
        this as unknown as ResizeObserver,
      );
    }
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
});

const trend: TireTrend = {
  points: [
    { km: 100000, actual: 8.0 },
    { km: 115000, actual: 6.5 },
    { km: 130000, actual: 5.0 },
  ],
  projection: [
    { km: 130000, projected: 5.0 },
    { km: 164000, projected: 1.6 },
  ],
  reference_mm: 1.6,
  projection_date: '2025-03-01',
};

describe('TireTrendChart', () => {
  it('renders without throwing given trend points and a projection', () => {
    const { container } = render(<TireTrendChart trend={trend} />);
    expect(container).toBeTruthy();
    // The recharts responsive wrapper is present in the DOM.
    expect(container.querySelector('.recharts-responsive-container')).not.toBeNull();
  });

  it('renders with empty data (no projection) without throwing', () => {
    const empty: TireTrend = {
      points: [],
      projection: [],
      reference_mm: 1.6,
      projection_date: null,
    };
    const { container } = render(<TireTrendChart trend={empty} />);
    expect(container).toBeTruthy();
  });
});
