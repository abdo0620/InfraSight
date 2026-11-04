// The final film for the judges: short trailer, logo transition and live demo recording (film_frames), then a short
// outro: 3:00 in all.
// Music: the inspired track under the trailer, climaxing on the cut and fading out during the transition; then the same
// sound, calmer and quieter, fading back in under the live demo; then a short closing phrase under the outro.
import React from 'react';
import {AbsoluteFill, Audio, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import timeline from './timeline_short.json';
import {SHORT_TOTAL, TrailerShort} from './TrailerShort';
import {LogoSting} from './scenes/LogoSting';
import {Outro} from './scenes/Outro';

const STING = timeline.sting_frames;
export const DEMO_FROM = SHORT_TOTAL + STING;
export const FILM_FRAMES = timeline.film_frames;                 // everything before the outro
export const DEMO_FRAMES = FILM_FRAMES - DEMO_FROM;               // the live demo is assembled to this length
export const OUTRO_FRAMES = timeline.outro_frames;
export const FINAL_TOTAL = FILM_FRAMES + OUTRO_FRAMES;

const OutroFaded: React.FC = () => {
	const frame = useCurrentFrame();
	const op = interpolate(frame, [0, 10, OUTRO_FRAMES - 24, OUTRO_FRAMES - 2], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<AbsoluteFill style={{background: '#000'}}>
			<AbsoluteFill style={{opacity: op}}>
				<Outro />
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

export const FinalVideo: React.FC = () => (
	<AbsoluteFill style={{background: '#000'}}>
		<Sequence from={0} durationInFrames={SHORT_TOTAL} name="Trailer">
			<TrailerShort />
		</Sequence>
		<Sequence from={SHORT_TOTAL} durationInFrames={STING} name="Logo transition">
			<LogoSting quiet />
		</Sequence>
		<Sequence from={DEMO_FROM} durationInFrames={DEMO_FRAMES} name="Live demo">
			<OffthreadVideo src={staticFile('live/live_demo.mp4')} muted />
		</Sequence>
		<Sequence from={FILM_FRAMES} durationInFrames={OUTRO_FRAMES} name="Outro">
			<OutroFaded />
		</Sequence>
		<Sequence from={0} durationInFrames={DEMO_FROM} layout="none" name="Music: trailer">
			<Audio src={staticFile('music/final_trailer.wav')} />
		</Sequence>
		<Sequence from={DEMO_FROM} durationInFrames={DEMO_FRAMES} layout="none" name="Music: demo bed">
			<Audio src={staticFile('music/final_demo_bed.wav')} volume={0.35} />
		</Sequence>
		<Sequence from={FILM_FRAMES} durationInFrames={OUTRO_FRAMES} layout="none" name="Music: outro">
			<Audio src={staticFile('music/final_outro.wav')} volume={0.8} />
		</Sequence>
		<Sequence from={FILM_FRAMES + 2} durationInFrames={54} layout="none" name="sfx impact">
			<Audio src={staticFile('sfx/impact.wav')} volume={0.3} />
		</Sequence>
	</AbsoluteFill>
);
