import { afterEach, describe, expect, it } from 'vitest';
import { formatMoney, formatNumber, formatPrice } from '@/lib/format';

afterEach(() => {
  localStorage.clear();
});

/** Normalize to digits + a single '.' decimal separator, dropping spaces/symbols. */
function norm(s: string): string {
  return s
    .replace(/ /g, '')
    .replace(/[^0-9.,]/g, '')
    .replace(',', '.');
}

/** Count fractional digits in a formatted number string. */
function fractionDigits(s: string): number {
  const m = norm(s).match(/\.(\d+)/);
  return m ? m[1].length : 0;
}

describe('formatMoney', () => {
  it('renders at most 2 decimal places', () => {
    expect(norm(formatMoney(1234.56))).toContain('1234.56');
    expect(fractionDigits(formatMoney(1234.56))).toBe(2);
  });

  it('returns an em dash for null', () => {
    expect(formatMoney(null)).toBe('—');
  });
});

describe('formatPrice', () => {
  it('renders exactly 4 decimal places (price per liter)', () => {
    expect(norm(formatPrice(1.689))).toContain('1.6890');
    expect(fractionDigits(formatPrice(1.689))).toBe(4);
  });

  it('pads short values to 4 decimals', () => {
    expect(fractionDigits(formatPrice(1.5))).toBe(4);
  });

  it('returns an em dash for null', () => {
    expect(formatPrice(null)).toBe('—');
  });
});

describe('formatNumber', () => {
  it('defaults to exactly 1 decimal (consumption / liters)', () => {
    expect(fractionDigits(formatNumber(6.2))).toBe(1);
    expect(norm(formatNumber(6.2))).toBe('6.2');
  });

  it('honors an explicit digit count', () => {
    expect(fractionDigits(formatNumber(2.31, 1))).toBe(1);
  });
});
