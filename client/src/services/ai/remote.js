// Real implementation: calls your backend (see docs/API.md for the contract).
import { AI } from '../../config.js';
import { toBlob, dataUrlToCanvas, maskArea } from './image.js';

async function post(url, form) {
  const res = await fetch(url, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`${url} returned ${res.status}`);
  return res.json();
}

async function imageAndMask(image, seg) {
  const f = new FormData();
  f.append('image', await toBlob(image, 'image/jpeg'));
  f.append('mask', await toBlob(seg.mask));
  return f;
}

export async function segmentDamage(image, point) {
  const f = new FormData();
  f.append('image', await toBlob(image, 'image/jpeg'));
  f.append('point', JSON.stringify(point));
  const mask = await dataUrlToCanvas((await post(AI.endpoints.segment, f)).mask);
  return { mask, areaRatio: maskArea(mask) };
}

export async function assessDamage(image, seg) {
  return post(AI.endpoints.assess, await imageAndMask(image, seg));
}

export async function repairImage(image, seg) {
  return dataUrlToCanvas((await post(AI.endpoints.repair, await imageAndMask(image, seg))).image);
}
