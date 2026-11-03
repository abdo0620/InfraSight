// Scene 15: name, repository and the hackathon.
import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Appear, C, Radar, SERIF, Stage} from '../lib';

export const Outro: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const pop = spring({frame, fps, config: {damping: 14}});
	return (
		<Stage>
			<div style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
				<div style={{display: 'flex', alignItems: 'center', gap: 34, transform: `scale(${0.85 + 0.15 * pop})`, opacity: pop}}>
					<Radar size={150} spin={frame * 5} />
					<div style={{fontFamily: SERIF, fontSize: 140, fontWeight: 500, letterSpacing: '-.02em'}}>InfraSight</div>
				</div>
				<Appear delay={14}>
					<div style={{fontSize: 44, color: C.text, marginTop: 26}}>One photo in. A decision-ready case out.</div>
				</Appear>
				<Appear delay={30}>
					<div style={{marginTop: 46, padding: '16px 34px', borderRadius: 999, background: '#111113', border: '1px solid rgba(255,255,255,.14)', fontSize: 40, fontFamily: 'ui-monospace, Consolas, monospace', color: '#f7c3ae'}}>
						github.com/abdo0620/InfraSight
					</div>
				</Appear>
				<Appear delay={46}>
					<div style={{fontSize: 30, color: C.muted, marginTop: 40, letterSpacing: '.02em'}}>Built for the Meta Global AI Developer Hackathon</div>
				</Appear>
			</div>
		</Stage>
	);
};
