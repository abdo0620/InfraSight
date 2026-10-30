// Browser-only simulation of the three pipeline steps. Same signatures as remote.js.
import { wait, clamp, newCanvas, maskArea } from './image.js';

// Step 1: SAM 3.1 stand-in. point = {x, y} in 0..1
export async function segmentDamage(image, point) {
  await wait(900);
  const { width: w, height: h } = image;
  const mask = newCanvas(w, h);
  const g = mask.getContext('2d');
  const cx = point.x * w, cy = point.y * h, rx = w * 0.13, ry = h * 0.085, n = 36;
  g.beginPath();
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * Math.PI * 2;
    const k = 1 + 0.18 * Math.sin(a * 3 + 1.3) + 0.1 * Math.sin(a * 5 + 0.4);
    const x = cx + Math.cos(a) * rx * k, y = cy + Math.sin(a) * ry * k;
    i ? g.lineTo(x, y) : g.moveTo(x, y);
  }
  g.closePath();
  g.fillStyle = '#fff';
  g.fill();
  return { mask, areaRatio: maskArea(mask) };
}

// Step 2: Muse Spark stand-in
export async function assessDamage(image, seg) {
  await wait(1100);
  const severity = clamp(Math.round(2 + seg.areaRatio * 90), 1, 10);
  return {
    damage_type: 'Road surface damage',
    severity,
    tripping_hazard: severity >= 7 ? 'High' : severity >= 4 ? 'Moderate' : 'Low',
    exposed_materials: ['Gravel base', 'Aggregate'],
    accessibility_impact: severity >= 6 ? 'Blocks wheelchair and stroller passage' : 'Uneven surface, minor obstruction',
    recommended_action: severity >= 7 ? 'Cordon off and repair within 48 hours' : severity >= 4 ? 'Schedule patch repair within 2 weeks' : 'Add to routine maintenance',
    priority: severity >= 7 ? 'Urgent' : severity >= 4 ? 'Standard' : 'Low',
  };
}

// Step 3: Muse Image stand-in (fills the mask with the surrounding color)
export async function repairImage(image, seg) {
  await wait(1300);
  const { width: w, height: h } = image;
  const src = image.getContext('2d').getImageData(0, 0, w, h).data;
  const m = seg.mask.getContext('2d').getImageData(0, 0, w, h).data;
  let minX = w, minY = h, maxX = 0, maxY = 0;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (m[(y * w + x) * 4 + 3] > 127) { minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y); }
  }
  const pad = 0.4, bw = maxX - minX, bh = maxY - minY;
  let r = 0, gg = 0, b = 0, c = 0;
  for (let y = Math.max(0, (minY - bh * pad) | 0); y < Math.min(h, maxY + bh * pad); y++)
    for (let x = Math.max(0, (minX - bw * pad) | 0); x < Math.min(w, maxX + bw * pad); x++) {
      const i = (y * w + x) * 4;
      if (m[i + 3] < 10) { r += src[i]; gg += src[i + 1]; b += src[i + 2]; c++; }
    }
  const avg = c ? `rgb(${(r / c) | 0},${(gg / c) | 0},${(b / c) | 0})` : '#888';
  const patch = newCanvas(w, h);
  const p = patch.getContext('2d');
  p.drawImage(seg.mask, 0, 0);
  p.globalCompositeOperation = 'source-in';
  p.fillStyle = avg;
  p.fillRect(0, 0, w, h);
  const out = newCanvas(w, h);
  const o = out.getContext('2d');
  o.drawImage(image, 0, 0);
  o.filter = 'blur(3px)';
  o.drawImage(patch, 0, 0);
  return out;
}
