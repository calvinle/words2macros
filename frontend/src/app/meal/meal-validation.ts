// Runtime check of the /analyze response, mirroring the Pydantic rules in
// src/words2macros/models.py. TypeScript types vanish when the app is built, so
// this is what stops a malformed response from reaching the page.

import { AnalyzeResponse, MAX_ITEMS_PER_MEAL, WARNING_CODES } from './meal.models';

export class ValidationError extends Error {}

type Obj = Record<string, unknown>;

function fail(path: string, problem: string): never {
  throw new ValidationError(`${path}: ${problem}`);
}

function object(v: unknown, path: string): Obj {
  if (typeof v !== 'object' || v === null || Array.isArray(v)) fail(path, 'expected an object');
  return v as Obj;
}

function array(v: unknown, path: string): unknown[] {
  if (!Array.isArray(v)) fail(path, 'expected a list');
  return v;
}

function text(v: unknown, path: string, { optional = false } = {}): void {
  if (optional && v === null) return;
  if (typeof v !== 'string' || v.trim() === '') fail(path, 'expected non-empty text');
}

function amount(v: unknown, path: string, { optional = false } = {}): number | null {
  if (optional && v === null) return null;
  if (typeof v !== 'number' || !Number.isFinite(v)) fail(path, 'expected a number');
  if (v < 0) fail(path, 'must not be negative');
  return v;
}

function oneOf(v: unknown, path: string, allowed: readonly unknown[]): void {
  if (!allowed.includes(v)) fail(path, `expected one of ${allowed.join(', ')}`);
}

function nutrients(v: unknown, path: string): void {
  const n = object(v, path);
  for (const f of ['calories_kcal', 'protein_g', 'carbs_g', 'fat_g', 'alcohol_g']) {
    amount(n[f], `${path}.${f}`);
  }
  const fiber = amount(n['fiber_g'], `${path}.fiber_g`, { optional: true });
  if (fiber !== null && fiber > (n['carbs_g'] as number)) {
    fail(`${path}.fiber_g`, 'is part of carbs_g, so it cannot exceed it');
  }
}

function item(v: unknown, path: string): void {
  const i = object(v, path);
  text(i['name'], `${path}.name`);
  text(i['preparation'], `${path}.preparation`, { optional: true });
  if (!amount(i['grams'], `${path}.grams`)) fail(`${path}.grams`, 'must be more than 0');
  oneOf(i['amount_source'], `${path}.amount_source`, ['stated', 'estimated']);
  text(i['assumption'], `${path}.assumption`, { optional: true });
  if (i['amount_source'] === 'estimated' && i['assumption'] === null) {
    fail(`${path}.assumption`, 'an estimated amount must state its assumption');
  }

  const m = object(i['match'], `${path}.match`);
  oneOf(m['source'], `${path}.match.source`, ['usda', 'ai_estimate']);
  if (m['source'] === 'usda' || m['fdc_id'] !== null) {
    if (!Number.isInteger(m['fdc_id'])) fail(`${path}.match.fdc_id`, 'expected a record ID');
  }
  text(m['description'], `${path}.match.description`);
  nutrients(m['per_100g'], `${path}.match.per_100g`);
  nutrients(i['nutrients'], `${path}.nutrients`);
}

/** The response, typed, if it has the expected shape; otherwise a ValidationError. */
export function validateAnalyzeResponse(data: unknown): AnalyzeResponse {
  const r = object(data, 'response');

  const items = array(r['items'], 'items');
  if (items.length < 1 || items.length > MAX_ITEMS_PER_MEAL) {
    fail('items', `expected 1 to ${MAX_ITEMS_PER_MEAL} foods`);
  }
  items.forEach((v, i) => item(v, `items[${i}]`));
  nutrients(r['totals'], 'totals');

  array(r['warnings'], 'warnings').forEach((v, i) => {
    const w = object(v, `warnings[${i}]`);
    oneOf(w['code'], `warnings[${i}].code`, WARNING_CODES);
    text(w['message'], `warnings[${i}].message`);
    const index = w['item_index'];
    if (index !== null && !(Number.isInteger(index) && (index as number) >= 0)) {
      fail(`warnings[${i}].item_index`, 'expected a food position or null');
    }
  });

  if (typeof r['text'] !== 'string') fail('text', 'expected text');
  text(r['request_id'], 'request_id');
  text(r['analyzed_at'], 'analyzed_at');
  return data as AnalyzeResponse;
}
