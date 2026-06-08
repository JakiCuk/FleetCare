import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { DashboardCar } from '@/types';
import { CarCard } from '@/pages/dashboard/CarCard';

function makeCar(overrides: Partial<DashboardCar> = {}): DashboardCar {
  return {
    id: 1,
    name: 'Škoda Octavia',
    license_plate: 'BA123AB',
    current_odometer_km: 127540,
    chips: [
      { label: 'STK', days_left: 12 },
      { label: 'PZP', days_left: 187 },
    ],
    next_service: 'Olej za 800 km',
    tires: 'Zima · 4.2 mm',
    overdue: false,
    ...overrides,
  };
}

function renderCard(car: DashboardCar) {
  return render(
    <MemoryRouter>
      <CarCard car={car} />
    </MemoryRouter>,
  );
}

describe('CarCard', () => {
  it('renders the car name, plate and its chips', () => {
    renderCard(makeCar());
    expect(screen.getByText('Škoda Octavia')).toBeInTheDocument();
    expect(screen.getByText('BA123AB')).toBeInTheDocument();
    // Chips render the label and a `Xd` suffix via StatusChip.
    expect(screen.getByText('STK')).toBeInTheDocument();
    expect(screen.getByText('12d')).toBeInTheDocument();
    expect(screen.getByText('PZP')).toBeInTheDocument();
  });

  it('shows the OVERDUE badge and a red border when overdue', () => {
    const { container } = renderCard(makeCar({ overdue: true }));
    expect(screen.getByText('OVERDUE')).toBeInTheDocument();
    // The card root is the <a> rendered by react-router's Link.
    const link = container.querySelector('a');
    expect(link).not.toBeNull();
    expect(link).toHaveClass('border-state-red');
  });

  it('hides the OVERDUE badge and uses the default border when not overdue', () => {
    const { container } = renderCard(makeCar({ overdue: false }));
    expect(screen.queryByText('OVERDUE')).not.toBeInTheDocument();
    const link = container.querySelector('a');
    expect(link).toHaveClass('border-border');
  });
});
