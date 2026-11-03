// Scene 2: the radar logo draws itself, the name and the tagline arrive.
import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Appear, C, Radar, SERIF, Stage} from '../lib';

export const LogoReveal: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const draw = interpolate(frame, [0, 26], [0, 1], {extrapolateRight: 'clamp'});
	const pop = spring({frame, fps, config: {damping: 12, mass: 0.7}});
	const name = 'InfraSight';
	return (
		<Stage>
			<div style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
				<div style={{display: 'flex', alignItems: 'center', gap: 40, transform: `scale(${0.8 + 0.2 * pop})`}}>
					<Radar size={190} draw={draw} spin={frame * 5} />
					<div style={{fontFamily: SERIF, fontSize: 170, fontWeight: 500, letterSpacing: '-.02em'}}>
						{name.split('').map((ch, i) => {
							const p = spring({frame: frame - 10 - i * 2, fps, config: {damping: 16}});
							return (
								<span key={i} style={{display: 'inline-block', opacity: p, transform: `translateY(${(1 - p) * 50}px)`}}>
									{ch}
								</span>
							);
						})}
					</div>
				</div>
				<Appear delay={40} y={20}>
					<div style={{fontSize: 52, color: C.text, marginTop: 34, letterSpacing: '-.01em'}}>The AI co-pilot for city streets.</div>
				</Appear>
				<Appear delay={58} y={14}>
					<div style={{fontSize: 30, color: C.muted, marginTop: 18, letterSpacing: '.04em'}}>Muse Spark · SAM 3.1 · Muse Image</div>
				</Appear>
			</div>
		</Stage>
	);
};
