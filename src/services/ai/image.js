// Canvas helpers shared by the mock and remote implementations.
export const wait = (ms) => new Promise((r) => setTimeout(r, ms));
export const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
export const newCanvas = (w, h) => Object.assign(document.createElement('canvas'), { width: w, height: h });
export const toBlob = (c, type = 'image/png') => new Promise((r) => c.toBlob(r, type, 0.9));

export async function dataUrlToCanvas(url) {
  const img = new Image();
  img.src = url;
  await img.decode();
  const c = newCanvas(img.width, img.height);
  c.getContext('2d').drawImage(img, 0, 0);
  return c;
}

export async function prepareImage(file, maxSide = 1024) {
  const img = new Image();
  img.src = URL.createObjectURL(file);
  await img.decode();
  const s = Math.min(1, maxSide / Math.max(img.width, img.height));
  const c = newCanvas(Math.round(img.width * s), Math.round(img.height * s));
  c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
  return c;
}

export function maskArea(mask) {
  const d = mask.getContext('2d').getImageData(0, 0, mask.width, mask.height).data;
  let n = 0;
  for (let i = 3; i < d.length; i += 4) if (d[i] > 127) n++;
  return n / (mask.width * mask.height);
}

export function overlayMask(image, seg) {
  const out = newCanvas(image.width, image.height);
  const o = out.getContext('2d');
  o.drawImage(image, 0, 0);
  const tint = newCanvas(image.width, image.height);
  const t = tint.getContext('2d');
  t.drawImage(seg.mask, 0, 0);
  t.globalCompositeOperation = 'source-in';
  t.fillStyle = 'rgba(255,80,60,.6)';
  t.fillRect(0, 0, tint.width, tint.height);
  o.drawImage(tint, 0, 0);
  return out;
}

export function thumbnail(image, width = 96) {
  const c = newCanvas(width, Math.round((image.height / image.width) * width));
  c.getContext('2d').drawImage(image, 0, 0, c.width, c.height);
  return c.toDataURL('image/jpeg', 0.7);
}
