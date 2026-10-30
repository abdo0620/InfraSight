// Public API of the AI pipeline. Features import from here, never from mock/remote directly.
import { AI } from '../../config.js';
import * as mock from './mock.js';
import * as remote from './remote.js';

const impl = () => (AI.useMock ? mock : remote);

export const segmentDamage = (image, point) => impl().segmentDamage(image, point);
export const assessDamage = (image, seg) => impl().assessDamage(image, seg);
export const repairImage = (image, seg) => impl().repairImage(image, seg);
export { prepareImage, overlayMask, thumbnail } from './image.js';
