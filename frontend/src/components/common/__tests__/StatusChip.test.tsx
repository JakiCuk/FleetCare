import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusChip } from '@/components/common/StatusChip';

describe('StatusChip', () => {
  it('renders the label and the day count suffix', () => {
    render(<StatusChip label="STK" days={12} />);
    expect(screen.getByText('STK')).toBeInTheDocument();
    expect(screen.getByText('12d')).toBeInTheDocument();
  });

  it('renders an em dash when days is null', () => {
    render(<StatusChip label="PZP" days={null} />);
    expect(screen.getByText('PZP')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('uses the red variant class for urgent (<= 7 days)', () => {
    const { container } = render(<StatusChip label="SK" days={4} />);
    expect(container.firstChild).toHaveClass('text-state-red');
    expect(container.firstChild).toHaveClass('bg-state-red-bg');
  });

  it('uses the yellow variant class in the 8..30 day band', () => {
    const { container } = render(<StatusChip label="STK" days={20} />);
    expect(container.firstChild).toHaveClass('text-state-yellow');
    expect(container.firstChild).toHaveClass('bg-state-yellow-bg');
  });

  it('uses the green variant class beyond 30 days', () => {
    const { container } = render(<StatusChip label="PZP" days={120} />);
    expect(container.firstChild).toHaveClass('text-state-green');
  });

  it('uses the gray variant class for null', () => {
    const { container } = render(<StatusChip label="KASKO" days={null} />);
    expect(container.firstChild).toHaveClass('text-state-gray');
  });
});
