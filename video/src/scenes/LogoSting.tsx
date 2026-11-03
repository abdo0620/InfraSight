// A short logo transition (3 s) between the trailer and the live demo recording: the radar draws and sweeps,
// the name lands, "Live demo" appears, then everything pushes in and fades to black.
import React from 'react';
import {Audio, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, Radar, SERIF, Stage} from '../lib';

export const STING_FRAMES = 90;

/** quiet: the softer effect levels used in the final film */
export const LogoSting: React.FC<{quiet?: boolean}> = ({quiet}) => {
	const v = quiet ? 0.4 : 1;
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const draw = interpolate(frame, [0, 22], [0, 1], {extrapolateRight: 'clamp'});
	const pop = spring({frame: frame - 4, fps, config: {damping: 14, mass: 0.7}});
	const word = spring({frame: frame - 16, fps, config: {damping: 18}});
	const live = spring({frame: frame - 30, fps, config: {damping: 16}});
	// the end: push in towards the radar and fade to black, so the recording can start from black
	const push = interpolate(frame, [62, STING_FRAMES], [1, 1.35], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const out = interpolate(frame, [68, STING_FRAMES - 4], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const fadeIn = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
	return (
		<Stage>
			<div style={{position: 'absolute', inset: 0, opacity: out * fadeIn, transform: `scale(${push})`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
				<div style={{display: 'flex', alignItems: 'center', gap: 36}}>
					<div style={{transform: `scale(${0.6 + 0.4 * pop}) rotate(${(1 - pop) * -40}deg)`}}>
						<Radar size={170} draw={draw} spin={frame * 7} />
					</div>
					<div style={{fontFamily: SERIF, fontSize: 150, fontWeight: 500, letterSpacing: '-.02em', opacity: word, transform: `translateX(${(1 - word) * 60}px)`}}>
						InfraSight
					</div>
				</div>
				<div style={{marginTop: 34, display: 'flex', alignItems: 'center', gap: 16, opacity: live, transform: `translateY(${(1 - live) * 20}px)`}}>
					<span style={{width: 16, height: 16, borderRadius: '50%', background: C.sev[4], boxShadow: `0 0 ${12 + 8 * Math.sin(frame / 4)}px ${C.sev[4]}`}} />
					<span style={{fontSize: 44, letterSpacing: '.22em', textTransform: 'uppercase', fontWeight: 700}}>Live demo</span>
				</div>
				<div style={{marginTop: 18, fontSize: 30, color: C.muted, opacity: live}}>The real app · real Meta model calls</div>
			</div>
			<Sequence from={0} layout="none">
				<Audio src={staticFile('sfx/shimmer.wav')} volume={0.8 * v} />
			</Sequence>
			<Sequence from={14} layout="none">
				<Audio src={staticFile('sfx/impact.wav')} volume={0.6 * v} />
			</Sequence>
			<Sequence from={60} layout="none">
				<Audio src={staticFile('sfx/whoosh.wav')} volume={0.9 * v} />
			</Sequence>
		</Stage>
	);
};
