import { esc } from '../dom.js';

export const pageHeader = (title, subtitle = '') => `<h1>${esc(title)}</h1><p>${esc(subtitle)}</p>`;
