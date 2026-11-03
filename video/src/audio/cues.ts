// Every sound effect, pinned to the frame of its scene where the thing happens on screen (frames taken from the scene
// code: cursor clicks at the click frame + 5, when the ripple shows; typing spans from useTyped start and length).
import timeline from '../timeline.json';

export type Sfx = 'whoosh' | 'swoosh' | 'click' | 'typing' | 'pop' | 'shimmer' | 'impact';
/** [scene, frame in the scene, effect, volume 0-1, length in frames (typing only)] */
type Cue = [string, number, Sfx, number?, number?];

// length of each effect file, in frames at 30 fps (public/sfx, made by audio/make_sfx.py)
export const SFX_FRAMES: Record<Sfx, number> = {whoosh: 21, swoosh: 14, click: 2, typing: 180, pop: 5, shimmer: 66, impact: 54};

const CUES: Cue[] = [
	// hook: each line lands, the strike-through draws, the question hits
	['Hook', 0, 'pop', 0.7], ['Hook', 44, 'pop', 0.7], ['Hook', 100, 'swoosh', 0.8], ['Hook', 128, 'impact', 0.8],
	// logo: the radar draws, name, tagline, models
	['LogoReveal', 0, 'shimmer', 1], ['LogoReveal', 10, 'pop', 0.6], ['LogoReveal', 40, 'pop', 0.6], ['LogoReveal', 58, 'pop', 0.5],
	// citizen report: photo dropped, address typed, suggestion picked, description typed, send, then the live AI panel
	['ReportPipeline', 21, 'click', 1], ['ReportPipeline', 22, 'pop', 0.6], ['ReportPipeline', 35, 'click', 1],
	['ReportPipeline', 34, 'typing', 0.8, 18], ['ReportPipeline', 52, 'pop', 0.5], ['ReportPipeline', 59, 'click', 1],
	['ReportPipeline', 75, 'click', 1], ['ReportPipeline', 72, 'typing', 0.8, 39], ['ReportPipeline', 109, 'click', 1],
	['ReportPipeline', 120, 'whoosh', 0.7], ['ReportPipeline', 186, 'pop', 0.8], ['ReportPipeline', 244, 'swoosh', 0.7],
	['ReportPipeline', 246, 'pop', 0.8], ['ReportPipeline', 304, 'shimmer', 0.6], ['ReportPipeline', 306, 'pop', 0.8],
	['ReportPipeline', 312, 'pop', 0.4],
	// map: legend chips, then the incident card
	['MapScene', 20, 'pop', 0.5],
	['MapScene', 70, 'pop', 0.8],
	// ticket: the cursor grabs the slider and sweeps it; the three images line up
	['TicketSlider', 23, 'click', 1], ['TicketSlider', 22, 'swoosh', 0.55], ['TicketSlider', 70, 'swoosh', 0.55],
	['TicketSlider', 40, 'pop', 0.6],
	['TicketSlider', 54, 'pop', 0.6], ['TicketSlider', 68, 'pop', 0.6],
	// full report: click, live steps, then the report cards and the cost rows
	['FullReport', 17, 'click', 1], ['FullReport', 16, 'pop', 0.6], ['FullReport', 34, 'pop', 0.6], ['FullReport', 84, 'pop', 0.7],
	['FullReport', 98, 'pop', 0.6], ['FullReport', 112, 'whoosh', 0.6], ['FullReport', 122, 'pop', 0.5], ['FullReport', 136, 'pop', 0.5],
	// detour: closed street, route drawing, the order typing itself
	['Detour', 14, 'swoosh', 0.7], ['Detour', 36, 'whoosh', 0.55], ['Detour', 66, 'swoosh', 0.5], ['Detour', 92, 'pop', 0.5],
	['Detour', 96, 'typing', 0.75, 140],
	// duplicates: two cards, the merge, one ticket
	['Duplicates', 2, 'pop', 0.7], ['Duplicates', 10, 'pop', 0.7], ['Duplicates', 52, 'whoosh', 0.7], ['Duplicates', 72, 'impact', 0.55],
	// stages: ticks forward, the draft types, the signature stamp
	['Stages', 27, 'pop', 0.5], ['Stages', 43, 'pop', 0.5], ['Stages', 62, 'typing', 0.75, 92], ['Stages', 150, 'impact', 0.5],
	// repair check: photos, scan line, verdict
	['RepairCheck', 4, 'pop', 0.6], ['RepairCheck', 14, 'pop', 0.6], ['RepairCheck', 40, 'swoosh', 0.6], ['RepairCheck', 96, 'pop', 0.9],
	// updates: one pop per message, then the language chips
	['Updates', 6, 'pop', 0.7], ['Updates', 24, 'pop', 0.7], ['Updates', 42, 'pop', 0.7], ['Updates', 60, 'pop', 0.7],
	['Updates', 86, 'pop', 0.4],
	// dashboard: matrix cells, the brief typing, the hotspot
	['Dashboard', 30, 'pop', 0.4], ['Dashboard', 50, 'typing', 0.7, 86], ['Dashboard', 120, 'pop', 0.6],
	// pdf: the pages fan out
	['PdfReport', 4, 'whoosh', 0.45], ['PdfReport', 8, 'pop', 0.6], ['PdfReport', 20, 'pop', 0.5],
	// powered by Meta: title shimmer, edges drawing, model cards, the result list
	['PoweredByMeta', 2, 'shimmer', 0.9], ['PoweredByMeta', 20, 'swoosh', 0.5], ['PoweredByMeta', 26, 'swoosh', 0.45],
	['PoweredByMeta', 32, 'swoosh', 0.45], ['PoweredByMeta', 30, 'pop', 0.7], ['PoweredByMeta', 48, 'pop', 0.7],
	['PoweredByMeta', 66, 'pop', 0.7], ['PoweredByMeta', 70, 'swoosh', 0.5], ['PoweredByMeta', 90, 'swoosh', 0.5],
	['PoweredByMeta', 112, 'swoosh', 0.45],
	['PoweredByMeta', 128, 'pop', 0.7], ['PoweredByMeta', 200, 'pop', 0.5],
	// outro: the final hit
	['Outro', 0, 'impact', 1], ['Outro', 2, 'shimmer', 0.7], ['Outro', 14, 'pop', 0.5], ['Outro', 30, 'pop', 0.6], ['Outro', 46, 'pop', 0.5],
];

export type PlacedCue = {from: number; sfx: Sfx; volume: number; frames: number};

/** Cues in video frames, plus a whoosh on every slide between scenes (just before the next scene starts). */
export const placeCues = (sceneStart: Record<string, number>): PlacedCue[] => {
	const placed: PlacedCue[] = CUES.map(([scene, f, sfx, volume = 1, frames]) => ({
		from: sceneStart[scene] + f,
		sfx,
		volume,
		frames: frames ?? SFX_FRAMES[sfx],
	}));
	timeline.scenes.forEach((s, i) => {
		const next = timeline.scenes[i + 1];
		if (next && s.into_next === 'slide') placed.push({from: sceneStart[next.name] - 3, sfx: 'whoosh', volume: 0.9, frames: SFX_FRAMES.whoosh});
		if (next && s.into_next === 'fade' && next.name === 'PdfReport') placed.push({from: sceneStart[next.name] - 3, sfx: 'whoosh', volume: 0.6, frames: SFX_FRAMES.whoosh});
	});
	return placed.sort((a, b) => a.from - b.from);
};

// how much each effect pushes the music down while it plays (ducking)
const WEIGHT: Record<Sfx, number> = {whoosh: 1, swoosh: 0.5, click: 0.15, typing: 0.35, pop: 0.3, shimmer: 0.9, impact: 1.4};

/** Music gain per frame: -2 dB per unit of effect activity, at most -6 dB, smoothed over a third of a second. */
export const duckCurve = (cues: PlacedCue[], total: number): number[] => {
	const act = new Array(total).fill(0);
	for (const c of cues)
		for (let f = Math.max(0, c.from - 2); f < Math.min(total, c.from + c.frames); f++) act[f] += WEIGHT[c.sfx] * c.volume;
	const smooth = act.map((_, f) => {
		let s = 0, n = 0;
		for (let k = f - 5; k <= f + 5; k++) if (k >= 0 && k < total) (s += act[k]), n++;
		return s / n;
	});
	return smooth.map((a) => 10 ** (-Math.min(6, 2 * a) / 20));
};
