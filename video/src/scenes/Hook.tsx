// Scene 1: the problem, in kinetic type.
import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Appear, C, SERIF, Stage} from '../lib';

const Line: React.FC<{text: string; start: number; end: number; size?: number; color?: string; strike?: boolean}> = ({text, start, end, size = 110, color = C.text, strike}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	if (frame < start - 2 || frame > end + 8) return null;
	const out = interpolate(frame, [end, end + 8], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const words = text.split(' ');
	const strikeP = strike ? interpolate(frame, [start + 16, start + 30], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 0;
	return (
		<div style={{position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', opacity: out}}>
			<div style={{position: 'relative', fontFamily: SERIF, fontSize: size, fontWeight: 500, letterSpacing: '-.025em', color, textAlign: 'center', maxWidth: 1600, lineHeight: 1.05}}>
				{words.map((w, i) => {
					const p = spring({frame: frame - start - i * 3, fps, config: {damping: 14, mass: 0.5}});
					return (
						<span key={i} style={{display: 'inline-block', marginRight: '0.24em', opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * 70}px) rotate(${(1 - p) * 4}deg)`}}>
							{w}
						</span>
					);
				})}
				{strike ? <div style={{position: 'absolute', left: 0, top: '55%', height: 8, borderRadius: 4, background: C.sev[4], width: `${strikeP * 100}%`}} /> : null}
			</div>
		</div>
	);
};

/** built: a first line saying what this is, for the final film */
export const Hook: React.FC<{built?: boolean}> = ({built}) => {
	const frame = useCurrentFrame();
	const zoom = interpolate(frame, [0, 180], [1, 1.06]);
	const p = (f: number) => Math.round(f * (built ? 0.68 : 1));    // the final film's short trailer runs the lines faster
	return (
		<Stage glow="rgba(239,68,68,.10)">
			<div style={{position: 'absolute', inset: 0, transform: `scale(${zoom})`}}>
				<Line text="A pothole next to a school." start={0} end={p(40) - (built ? 6 : 0)} />
				<Line text="Reported by email." start={p(44)} end={p(80) - (built ? 6 : 0)} color={C.muted} />
				<Line text="Lost for weeks." start={p(84)} end={p(124) - (built ? 6 : 0)} strike />
				<Line text="What if one photo was enough?" start={p(128)} end={200} color={C.clay} size={104} />
			</div>
			{built ? (
				<Appear delay={0} y={-12} style={{position: 'absolute', top: 54, left: 0, right: 0, textAlign: 'center'}}>
					<div style={{fontSize: 30, color: C.muted, letterSpacing: '.02em'}}>
						<span style={{color: C.text, fontWeight: 600}}>InfraSight</span>, built this week at the Meta Global AI Developer Hackathon
					</div>
				</Appear>
			) : null}
		</Stage>
	);
};
