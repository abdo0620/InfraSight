// Short trailer, last scene: the three Meta models that power the app, as chips popping in, then a hard cut to the logo.
import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Appear, C, SERIF, Stage} from '../lib';

const MODELS = [
	{name: 'Muse Spark', role: 'reads, triages, writes the reports', color: C.meta, at: 14},
	{name: 'SAM 3.1', role: 'outlines the damage', color: '#7c3aed', at: 24},
	{name: 'Muse Image', role: 'draws the street repaired', color: '#db2777', at: 34},
];

export const ModelBadges: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return (
		<Stage glow="rgba(4,103,223,.16)">
			<div style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
				<Appear delay={0} y={-16}>
					<div style={{fontSize: 24, fontWeight: 700, letterSpacing: '.18em', textTransform: 'uppercase', color: '#5b9cff', textAlign: 'center'}}>Meta Model API</div>
					<div style={{fontFamily: SERIF, fontSize: 92, fontWeight: 500, letterSpacing: '-.02em', marginTop: 4, textAlign: 'center'}}>Powered by Meta</div>
				</Appear>
				<div style={{display: 'flex', gap: 34, marginTop: 56}}>
					{MODELS.map((m) => {
						const p = spring({frame: frame - m.at, fps, config: {damping: 13, mass: 0.6}});
						return (
							<div
								key={m.name}
								style={{
									opacity: Math.min(1, p * 1.4),
									transform: `translateY(${(1 - p) * 40}px) scale(${0.85 + 0.15 * p})`,
									width: 470,
									background: '#0d0f14',
									border: `2px solid ${m.color}`,
									borderRadius: 24,
									padding: '24px 28px',
									boxShadow: `0 0 60px ${m.color}40`,
								}}
							>
								<div style={{display: 'flex', alignItems: 'center', gap: 14}}>
									<span style={{width: 16, height: 16, borderRadius: '50%', background: m.color}} />
									<span style={{fontSize: 44, fontWeight: 800}}>{m.name}</span>
								</div>
								<div style={{fontSize: 24, color: '#c9c9d1', marginTop: 10}}>{m.role}</div>
							</div>
						);
					})}
				</div>
				<Appear delay={52} y={14}>
					<div style={{fontSize: 30, color: C.muted, marginTop: 48}}>
						AI drafts. <span style={{color: C.text}}>People decide.</span>
					</div>
				</Appear>
			</div>
		</Stage>
	);
};
