// The whole trailer: every scene in order, joined by short fades and slides, with the soundtrack on top.
// Scene lengths live in timeline.json, shared with the soundtrack and the music scripts (audio/*.py).
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {linearTiming, springTiming, TransitionSeries} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import timeline from './timeline.json';
import {Soundtrack} from './audio/Soundtrack';
import {Hook} from './scenes/Hook';
import {LogoReveal} from './scenes/LogoReveal';
import {ReportPipeline} from './scenes/ReportPipeline';
import {MapScene} from './scenes/MapScene';
import {TicketSlider} from './scenes/TicketSlider';
import {FullReport} from './scenes/FullReport';
import {Detour} from './scenes/Detour';
import {Duplicates} from './scenes/Duplicates';
import {Stages} from './scenes/Stages';
import {RepairCheck} from './scenes/RepairCheck';
import {Updates} from './scenes/Updates';
import {Dashboard} from './scenes/Dashboard';
import {PdfReport} from './scenes/PdfReport';
import {PoweredByMeta} from './scenes/PoweredByMeta';
import {Outro} from './scenes/Outro';

const COMPONENTS: Record<string, React.FC> = {
	Hook, LogoReveal, ReportPipeline, MapScene, TicketSlider, FullReport, Detour, Duplicates, Stages, RepairCheck, Updates,
	Dashboard, PdfReport, PoweredByMeta, Outro,
};
const T = timeline.transition;

/** First frame of each scene in the finished video (a transition overlaps the end of one scene and the start of the next). */
export const SCENE_START: Record<string, number> = {};
let at = 0;
for (const s of timeline.scenes) {
	SCENE_START[s.name] = at;
	at += s.frames - (s.into_next === 'cut' ? 0 : T);
}
export const TOTAL = timeline.scenes.reduce((n, s) => n + s.frames, 0) - timeline.scenes.filter((s) => s.into_next !== 'cut').length * T;

/** version 0: no sound (the original render); 1: effects only; 2: generated music; 3: music inspired by the reference;
 * 4: laid-back cinematic hip-hop beat */
export type TrailerProps = {version: 0 | 1 | 2 | 3 | 4};

export const Trailer: React.FC<TrailerProps> = ({version}) => (
	<AbsoluteFill style={{background: '#000'}}>
		<TransitionSeries>
			{timeline.scenes.flatMap((s, i) => {
				const Scene = COMPONENTS[s.name];
				const items = [
					<TransitionSeries.Sequence key={`s${i}`} durationInFrames={s.frames}>
						<Scene />
					</TransitionSeries.Sequence>,
				];
				if (s.into_next !== 'cut' && i < timeline.scenes.length - 1)
					items.push(
						<TransitionSeries.Transition
							key={`t${i}`}
							presentation={s.into_next === 'slide' ? slide({direction: 'from-right'}) : fade()}
							timing={s.into_next === 'slide' ? springTiming({config: {damping: 200}, durationInFrames: T}) : linearTiming({durationInFrames: T})}
						/>,
					);
				return items;
			})}
		</TransitionSeries>
		{version !== 0 ? <Soundtrack version={version} /> : null}
	</AbsoluteFill>
);
