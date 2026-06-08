import { describe, expect, it } from 'vitest';
import {
  chipColors,
  intervalColor,
  treadColor,
  treadHex,
} from '@/lib/colors';

describe('chipColors', () => {
  it('returns gray for null/undefined', () => {
    expect(chipColors(null)).toBe('gray');
    expect(chipColors(undefined)).toBe('gray');
  });

  it('returns red for overdue (< 0) and within the default 7-day threshold', () => {
    expect(chipColors(-1)).toBe('red');
    expect(chipColors(0)).toBe('red');
    expect(chipColors(7)).toBe('red');
  });

  it('returns yellow for the 8..30 day band', () => {
    expect(chipColors(8)).toBe('yellow');
    expect(chipColors(30)).toBe('yellow');
  });

  it('returns green beyond 30 days', () => {
    expect(chipColors(31)).toBe('green');
    expect(chipColors(365)).toBe('green');
  });

  it('honors the stricter <=14 threshold used for STK/insurance in car detail', () => {
    // With urgentThreshold = 14, days up to 14 are red.
    expect(chipColors(8, 14)).toBe('red');
    expect(chipColors(14, 14)).toBe('red');
    expect(chipColors(15, 14)).toBe('yellow');
    expect(chipColors(30, 14)).toBe('yellow');
    expect(chipColors(31, 14)).toBe('green');
  });
});

describe('treadColor', () => {
  it('maps mm bands: <3 red, <5 yellow, else green; null -> gray', () => {
    expect(treadColor(null)).toBe('gray');
    expect(treadColor(undefined)).toBe('gray');
    expect(treadColor(2.9)).toBe('red');
    expect(treadColor(3)).toBe('yellow');
    expect(treadColor(4.9)).toBe('yellow');
    expect(treadColor(5)).toBe('green');
    expect(treadColor(8)).toBe('green');
  });
});

describe('treadHex', () => {
  it('returns the matching hex per tread band', () => {
    expect(treadHex(null)).toBe('#94a3b8');
    expect(treadHex(2)).toBe('#dc2626');
    expect(treadHex(4)).toBe('#ea580c');
    expect(treadHex(6)).toBe('#16a34a');
  });
});

describe('intervalColor', () => {
  it('red when km_left < 500 or days_left <= 14', () => {
    expect(intervalColor(400, 999)).toBe('red');
    expect(intervalColor(9999, 14)).toBe('red');
  });

  it('yellow when km_left < 2000 or days_left <= 30', () => {
    expect(intervalColor(1500, 999)).toBe('yellow');
    expect(intervalColor(9999, 30)).toBe('yellow');
  });

  it('green otherwise, including when both inputs are null', () => {
    expect(intervalColor(5000, 365)).toBe('green');
    expect(intervalColor(null, null)).toBe('green');
  });
});
