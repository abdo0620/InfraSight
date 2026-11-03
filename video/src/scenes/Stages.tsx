// Scene 9: the 7 legal stages of a repair, ticking forward, with an AI draft for the current stage.
import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Appear, C, Caption, Stage, useTyped, Window} from '../lib';

const STAGES = ['Intake and registration', 'Technical and financial study', 'Arbitration and decision', 'Public procurement', 'Authorizations', 'Execution and monitoring', 'Acceptance and closure'];
const DRAFT = `1. BUDGET IMPACT
- Estimate: €868–€928 excl. VAT, within the roads budget
2. DECISION
- Purchase order under the mayor's delegation (art. L2122-22 CGCT)
- No council vote needed
3. SIGNATURE
- Elected official: [to fill]`;

export const Stages: React.FC = () => {
	const frame = useCurrentFrame();
	const cur = Math.min(2, Math.floor(interpolate(frame, [10, 60], [0, 2.99], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})));
	const draft = useTyped(DRAFT, 62, 70);
	const stamp = interpolate(frame, [150, 160], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<Stage>
			<Caption kicker="The legal process" title="7 stages. An AI draft for each one." sub="Only an elected official can sign the decision." top={300} width={560} />
			<Window x={740} y={230} w={1080} h={600} zoom={1.42}>
				<div style={{display: 'grid', gridTemplateColumns: '250px 1fr', gap: 14}}>
					<div className="panel">
						<h2>Pipeline</h2>
						{STAGES.map((s, i) => (
							<div key={s} style={{display: 'flex', gap: 10, alignItems: 'center', padding: '6px 0', color: i <= cur ? C.text : C.muted}}>
								<span style={{width: 20, height: 20, borderRadius: '50%', display: 'grid', placeItems: 'center', fontSize: 11, fontWeight: 700, background: i < cur ? C.green : 'transparent', border: `2px solid ${i < cur ? C.green : i === cur ? C.clay : 'rgba(255,255,255,.15)'}`}}>
									{i < cur ? '✓' : ''}
								</span>
								<span style={{fontWeight: i === cur ? 700 : 400}}>{s}</span>
							</div>
						))}
					</div>
					<div className="panel" style={{position: 'relative'}}>
						<h2>Stage 3 · Arbitration and decision</h2>
						<div className="row" style={{marginTop: 4}}>
							<button className="btn">AI draft for this stage</button>
						</div>
						<div className="ao" style={{minHeight: 220}}>{draft}</div>
						<Appear delay={150} scale={1.6} y={0} style={{position: 'absolute', right: 18, bottom: 18}}>
							<div style={{transform: 'rotate(-8deg)', border: `3px solid ${C.clay}`, color: C.clay, borderRadius: 10, padding: '6px 12px', fontWeight: 800, letterSpacing: '.08em', opacity: stamp}}>SIGNED · ELECTED</div>
						</Appear>
					</div>
				</div>
			</Window>
		</Stage>
	);
};
