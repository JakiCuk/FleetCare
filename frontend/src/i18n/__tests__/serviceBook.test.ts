import { describe, expect, it } from 'vitest';
import sk from '@/i18n/sk.json';
import en from '@/i18n/en.json';

const PERFORMED = [
  'oilChangeService',
  'inspection',
  'withOilChange',
  'extendedScope',
  'longlifeOil',
  'cngCorrosion',
  'headlights',
  'repairRec',
  'customerRequest',
];

const ADDITIONAL = [
  'adblue',
  'brakeFluid',
  'fuelFilter',
  'gearOil',
  'haldex',
  'serpentine',
  'airFilter',
  'tyreSealant',
  'cabinFilter',
  'timingBelt',
  'sparkPlugs',
];

function flatten(obj: Record<string, unknown>, prefix = ''): Set<string> {
  const out = new Set<string>();
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === 'object') {
      for (const nested of flatten(v as Record<string, unknown>, key)) out.add(nested);
    } else {
      out.add(key);
    }
  }
  return out;
}

describe('service-book i18n', () => {
  const skSvc = sk.service as unknown as Record<string, Record<string, string>>;
  const enSvc = en.service as unknown as Record<string, Record<string, string>>;

  it('has every "performed" item in both SK and EN', () => {
    for (const key of PERFORMED) {
      expect(skSvc.performed[key], `sk service.performed.${key}`).toBeTruthy();
      expect(enSvc.performed[key], `en service.performed.${key}`).toBeTruthy();
    }
  });

  it('has every "additional" item in both SK and EN', () => {
    for (const key of ADDITIONAL) {
      expect(skSvc.additional[key], `sk service.additional.${key}`).toBeTruthy();
      expect(enSvc.additional[key], `en service.additional.${key}`).toBeTruthy();
    }
  });

  it('keeps full key parity between SK and EN locales', () => {
    const skKeys = flatten(sk as Record<string, unknown>);
    const enKeys = flatten(en as Record<string, unknown>);
    expect([...skKeys].filter((k) => !enKeys.has(k))).toEqual([]);
    expect([...enKeys].filter((k) => !skKeys.has(k))).toEqual([]);
  });
});
