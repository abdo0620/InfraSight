// Scene 14: how the three Meta models work together, as an animated diagram.
import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {Appear, C, SERIF, Stage} from '../lib';

type Edge = {d: string; from: number; label?: string; lx?: number; ly?: number};

const MODELS = [
	{name: 'Muse Spark', y: 214, color: C.meta, lines: ['Triage, duplicates, full report with cited rules,', 'cost work items, legal drafts, traffic order,', 'repair check, weekly brief, updates in 9 languages']},
	{name: 'SAM 3.1', y: 500, color: '#7c3aed', lines: ['Outlines the damage on the photo,', 'pixel by pixel']},
	{name: 'Muse Image', y: 726, color: '#db2777', lines: ['Draws the street repaired,', 'from the photo and the outline']},
];
const OUT = ['Report with sources', 'Sourced cost estimate', 'Detour + traffic order', 'Drafts for 7 legal stages', 'Updates to citizens', 'PDF incident report'];

const EDGES: Edge[] = [
	// from the citizen's photo (right edge 470, middle 575) to the middle of each model card
	{d: 'M470 575 C 600 575, 600 329, 720 329', from: 20},
	{d: 'M470 575 C 600 575, 600 585, 720 585', from: 26},
	{d: 'M470 575 C 600 575, 600 811, 720 811', from: 32},
	// between the model cards (Muse Spark ends near 446, SAM 3.1 near 672)
	{d: 'M920 448 L920 498', from: 70, label: 'names the damage', lx: 940, ly: 480},
	{d: 'M920 674 L920 724', from: 90, label: 'outline', lx: 940, ly: 706},
	// to the result card (left edge 1420, middle 480)
	{d: 'M1240 329 C 1330 329, 1330 480, 1420 480', from: 110},
	{d: 'M1240 585 C 1330 585, 1330 480, 1420 480', from: 116},
	{d: 'M1240 811 C 1330 811, 1330 480, 1420 480', from: 122},
];

export const PoweredByMeta: React.FC = () => {
	const frame = useCurrentFrame();
	return (
		<Stage glow="rgba(4,103,223,.16)">
			<Appear delay={0} y={-20} style={{position: 'absolute', top: 60, left: 0, right: 0, textAlign: 'center'}}>
				<div style={{fontSize: 24, fontWeight: 700, letterSpacing: '.18em', textTransform: 'uppercase', color: '#5b9cff'}}>Meta Model API</div>
				<div style={{fontFamily: SERIF, fontSize: 84, fontWeight: 500, letterSpacing: '-.02em', marginTop: 6}}>Powered by Meta</div>
			</Appear>
			<svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
				{EDGES.map((e, i) => {
					const p = interpolate(frame, [e.from, e.from + 22], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
					return (
						<g key={i}>
							<path d={e.d} stroke="rgba(255,255,255,.18)" strokeWidth={3} fill="none" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
							{p >= 1 ? <path d={e.d} stroke={C.clay} strokeWidth={3} fill="none" strokeDasharray="6 14" strokeDashoffset={-frame * 2} opacity={0.9} /> : null}
							{e.label && p > 0.5 ? (
								<text x={e.lx} y={e.ly} fill={C.muted} fontSize={22} fontFamily="Inter">
									{e.label}
								</text>
							) : null}
						</g>
					);
				})}
			</svg>
			<Appear delay={6} x={-40} y={0} style={{position: 'absolute', left: 110, top: 430}}>
				<div style={{width: 360, background: '#0f0f11', border: '1px solid rgba(255,255,255,.12)', borderRadius: 22, padding: 16}}>
					<Img src={staticFile('img/bus-photo.jpg')} style={{width: '100%', height: 170, objectFit: 'cover', borderRadius: 14}} />
					<div style={{fontSize: 26, fontWeight: 700, marginTop: 12}}>One photo + one sentence</div>
					<div style={{fontSize: 20, color: C.muted}}>from a citizen, pinned on the map</div>
				</div>
			</Appear>
			{MODELS.map((m, i) => (
				<Appear key={m.name} delay={30 + i * 18} scale={0.85} y={0} style={{position: 'absolute', left: 720, top: m.y}}>
					<div style={{width: 520, background: '#0d0f14', border: `2px solid ${m.color}`, borderRadius: 22, padding: '18px 24px', boxShadow: `0 0 50px ${m.color}33`}}>
						<div style={{display: 'flex', alignItems: 'center', gap: 12}}>
							<span style={{width: 14, height: 14, borderRadius: '50%', background: m.color}} />
							<span style={{fontSize: 38, fontWeight: 800}}>{m.name}</span>
						</div>
						<div style={{fontSize: 20, color: '#c9c9d1', marginTop: 8, lineHeight: 1.4}}>
							{m.lines.map((l) => (
								<div key={l}>{l}</div>
							))}
						</div>
					</div>
				</Appear>
			))}
			<Appear delay={128} x={40} y={0} style={{position: 'absolute', left: 1420, top: 330}}>
				<div style={{width: 420, background: '#0f0f11', border: `2px solid ${C.clay}`, borderRadius: 22, padding: '20px 24px'}}>
					<div style={{fontSize: 28, fontWeight: 800, marginBottom: 10}}>A decision-ready case</div>
					{OUT.map((o, i) => (
						<Appear key={o} delay={140 + i * 7} x={20} y={0}>
							<div style={{display: 'flex', gap: 12, alignItems: 'center', fontSize: 23, padding: '6px 0'}}>
								<span style={{color: '#86efac', fontWeight: 800}}>✓</span>
								{o}
							</div>
						</Appear>
					))}
				</div>
			</Appear>
			<Appear delay={200} y={20} style={{position: 'absolute', bottom: 54, left: 0, right: 0, textAlign: 'center'}}>
				<div style={{fontSize: 30, color: C.muted}}>
					AI drafts. <span style={{color: C.text}}>People decide.</span> Every legal point cites a source or says [verify].
				</div>
			</Appear>
		</Stage>
	);
};
