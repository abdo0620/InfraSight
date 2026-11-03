// The short trailer that opens the final film (~30 s): the trailer's scenes cut down, the AI waits skipped (each scene
// starts `skip` frames in), joined by quick fades. A numbered feature tracker along the bottom says which feature is on
// screen. Few, soft effects; the music is added by FinalVideo so it can run on through the logo transition.
import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {linearTiming, TransitionSeries} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import timeline from './timeline_short.json';
import {SFX_FRAMES, Sfx} from './audio/cues';
import {C} from './lib';
import {Hook} from './scenes/Hook';
import {LogoReveal} from './scenes/LogoReveal';
import {ReportPipeline} from './scenes/ReportPipeline';
import {TicketSlider} from './scenes/TicketSlider';
import {FullReport} from './scenes/FullReport';
import {Detour} from './scenes/Detour';
import {Duplicates} from './scenes/Duplicates';
import {Updates} from './scenes/Updates';
import {Dashboard} from './scenes/Dashboard';
import {ModelBadges} from './scenes/ModelBadges';

const COMPONENTS: Record<string, React.FC<{built?: boolean}>> = {
	Hook, LogoReveal, ReportPipeline, TicketSlider, FullReport, Detour, Duplicates, Updates, Dashboard, ModelBadges,
};
const T = timeline.transition;
type Scene = {name: string; frames: number; skip: number; into_next: string; feature?: string};
const SCENES = timeline.scenes as Scene[];

export const SHORT_START: Record<string, number> = {};
let at = 0;
for (const s of SCENES) {
	SHORT_START[s.name] = at;
	at += s.frames - (s.into_next === 'cut' ? 0 : T);
}
export const SHORT_TOTAL = at;

/** [scene, frame in the cut-down scene, effect, volume, length (typing only)]: few, soft, well under the music */
const CUES: [string, number, Sfx, number, number?][] = [
	['Hook', 0, 'pop', 0.3], ['Hook', 30, 'pop', 0.3], ['Hook', 68, 'swoosh', 0.3], ['Hook', 87, 'impact', 0.35],
	['LogoReveal', 0, 'shimmer', 0.4],
	['ReportPipeline', 46, 'swoosh', 0.3], ['ReportPipeline', 106, 'pop', 0.3],
	['TicketSlider', 3, 'click', 0.3], ['TicketSlider', 2, 'swoosh', 0.25], ['TicketSlider', 50, 'swoosh', 0.25],
	['FullReport', 2, 'pop', 0.25], ['FullReport', 26, 'pop', 0.25],
	['Detour', 6, 'whoosh', 0.3], ['Detour', 36, 'swoosh', 0.25], ['Detour', 66, 'typing', 0.22, 30],
	['Duplicates', 42, 'whoosh', 0.3],
	['Updates', 4, 'pop', 0.25], ['Updates', 22, 'pop', 0.25], ['Updates', 40, 'pop', 0.25],
	['Dashboard', 10, 'typing', 0.2, 50],
	['ModelBadges', 0, 'shimmer', 0.35], ['ModelBadges', 14, 'pop', 0.3], ['ModelBadges', 24, 'pop', 0.3], ['ModelBadges', 34, 'pop', 0.3],
];

const FEATURES = SCENES.filter((s) => s.feature);

/** The numbered feature checklist, under each scene's title on the left: the current feature lit in clay, the ones
 * already shown ticked. */
const Tracker: React.FC = () => {
	const frame = useCurrentFrame();
	const first = SHORT_START[FEATURES[0].name];
	const last = FEATURES[FEATURES.length - 1];
	const end = SHORT_START[last.name] + last.frames;
	if (frame < first - 4 || frame > end) return null;
	const op = interpolate(frame, [first - 4, first + 8, end - 10, end], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	let cur = 0;
	FEATURES.forEach((f, i) => {
		if (frame >= SHORT_START[f.name] + T / 2) cur = i;
	});
	return (
		<div style={{position: 'absolute', left: 104, bottom: 46, display: 'flex', flexDirection: 'column', gap: 7, opacity: op, fontFamily: 'Inter'}}>
			{FEATURES.map((f, i) => {
				const on = i === cur;
				const done = i < cur;
				return (
					<div key={f.name} style={{display: 'flex', alignItems: 'center', gap: 12, height: 34, whiteSpace: 'nowrap'}}>
						<span
							style={{
								width: 30, height: 30, borderRadius: '50%', display: 'grid', placeItems: 'center', fontSize: 16, fontWeight: 800,
								background: on ? C.clay : done ? 'rgba(255,255,255,.12)' : 'transparent',
								border: `1.5px solid ${on ? C.clay : done ? 'rgba(255,255,255,.25)' : 'rgba(255,255,255,.14)'}`,
								color: on ? '#1c0e08' : done ? '#86efac' : '#5d5d66',
							}}
						>
							{done ? '✓' : i + 1}
						</span>
						<span style={{fontSize: on ? 25 : 21, fontWeight: on ? 800 : 600, color: on ? C.text : done ? '#a1a1aa' : '#55555d'}}>{f.feature}</span>
					</div>
				);
			})}
		</div>
	);
};

export const TrailerShort: React.FC = () => (
	<AbsoluteFill style={{background: '#000'}}>
		<TransitionSeries>
			{SCENES.flatMap((s, i) => {
				const Scene = COMPONENTS[s.name];
				const items = [
					<TransitionSeries.Sequence key={`s${i}`} durationInFrames={s.frames}>
						<Sequence from={-s.skip}>
							<Scene built={s.name === 'Hook'} />
						</Sequence>
					</TransitionSeries.Sequence>,
				];
				if (s.into_next !== 'cut' && i < SCENES.length - 1)
					items.push(<TransitionSeries.Transition key={`t${i}`} presentation={fade()} timing={linearTiming({durationInFrames: T})} />);
				return items;
			})}
		</TransitionSeries>
		<Tracker />
		{CUES.map(([scene, f, sfx, volume, frames], i) => (
			<Sequence key={i} from={SHORT_START[scene] + f} durationInFrames={frames ?? SFX_FRAMES[sfx]} layout="none" name={`sfx ${sfx}`}>
				<Audio src={staticFile(`sfx/${sfx}.wav`)} volume={volume} />
			</Sequence>
		))}
	</AbsoluteFill>
);
