// Scene 10: acceptance. The after-repair photo is compared with the reported damage; the AI gives a verdict.
import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {Appear, C, Caption, Stage} from '../lib';

export const RepairCheck: React.FC = () => {
	const frame = useCurrentFrame();
	const scan = interpolate(frame, [40, 90], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const figs: [string, string][] = [
		['pothole-zone.jpg', 'Before · damage outlined'],
		['pothole-preview.jpg', 'After-repair photo (example)'],
	];
	return (
		<Stage glow="rgba(22,163,74,.12)">
			<Caption kicker="Repair check" title="Was it really fixed?" sub="At acceptance, Muse Spark compares the photos." top={330} width={520} />
			<div style={{position: 'absolute', left: 700, top: 200, display: 'flex', gap: 30}}>
				{figs.map(([f, t], i) => (
					<Appear key={f} delay={4 + i * 10} y={40}>
						<div style={{width: 540, position: 'relative'}}>
							<div style={{position: 'relative', borderRadius: 18, overflow: 'hidden'}}>
								<Img src={staticFile('img/' + f)} style={{width: '100%', height: 360, objectFit: 'cover', display: 'block'}} />
								<div style={{position: 'absolute', left: 0, right: 0, top: `${scan * 100}%`, height: 4, background: '#86efac', boxShadow: '0 0 24px #22c55e', opacity: scan > 0 && scan < 1 ? 1 : 0}} />
							</div>
							<div style={{fontSize: 24, marginTop: 12, color: C.muted}}>{t}</div>
						</div>
					</Appear>
				))}
			</div>
			<Appear delay={96} y={30} style={{position: 'absolute', left: 700, top: 690}}>
				<div style={{width: 1110, background: '#0f0f11', border: '1px solid rgba(34,197,94,.45)', borderRadius: 20, padding: '22px 28px', display: 'flex', gap: 22, alignItems: 'center'}}>
					<span style={{width: 56, height: 56, borderRadius: '50%', background: C.green, display: 'grid', placeItems: 'center', fontSize: 32, fontWeight: 800}}>✓</span>
					<div>
						<div style={{fontSize: 34, fontWeight: 700, color: '#86efac'}}>Verdict: repaired</div>
						<div style={{fontSize: 24, color: C.muted, marginTop: 4}}>The pothole is filled flush with the road. No remaining issue. Confirm on site.</div>
					</div>
				</div>
			</Appear>
		</Stage>
	);
};
