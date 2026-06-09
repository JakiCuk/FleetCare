import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import i18n from '@/i18n';
import { AddCarModal } from '@/pages/dashboard/AddCarModal';

function renderModal() {
  return render(<AddCarModal open onClose={() => {}} onCreated={() => {}} />);
}

describe('AddCarModal', () => {
  it('does not render a Name field (mockup parity)', () => {
    renderModal();
    const nameLabel = i18n.t('addCar.name');
    // The "Name" label must not be present in the create-car modal.
    expect(screen.queryByText(nameLabel)).not.toBeInTheDocument();
  });

  it('renders the make/model/year/plate/vin/odometer fields', () => {
    renderModal();
    for (const key of ['make', 'model', 'year', 'licensePlate', 'vin', 'odometer']) {
      const label = i18n.t(`addCar.${key}`);
      expect(screen.getByText(label), `field ${key}`).toBeInTheDocument();
    }
  });
});
