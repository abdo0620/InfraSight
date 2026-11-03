// Renders still frames of the trailer to check scenes without rendering the whole video.
// Usage: node scripts/stills.mjs <out dir> <frame> [<frame> ...]
import path from 'node:path';
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';

const [outDir, ...frames] = process.argv.slice(2);
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: 'Trailer'});
for (const f of frames.map(Number)) {
	const output = path.join(outDir, `f${String(f).padStart(4, '0')}.jpg`);
	await renderStill({serveUrl, composition, frame: f, output, imageFormat: 'jpeg', jpegQuality: 80, scale: 0.5});
	console.log('still', f);
}
