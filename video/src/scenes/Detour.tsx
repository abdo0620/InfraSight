// Scene 7: the closed street, the detour drawing itself on the map, and the mayor's traffic order being drafted.
import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {C, Caption, Stage, useTyped, Window} from '../lib';

// in the detour map image (549 x 258 px): the closed section (orange) and the detour (blue), traced from the app
const CLOSED = 'M282 76 L299 167';
const ROUTE = 'M282 76 L272 88 L247 115 L257 125 L260 160 L272 172 L290 185 L297 172';
const ORDER = `MUNICIPAL ORDER No. [to fill] on temporary traffic regulation – Avenue du Maréchal Foch

The Mayor of Brest,
Having regard to the General Code of Local Authorities (CGCT), articles L2213-1 and L2213-2;
Whereas a manhole cover sunken about 3 cm makes cars swerve on Avenue Foch (RD 14) [to check];
ORDERS
Article 1 – Avenue du Maréchal Foch is closed to traffic over about 200 m.
Article 2 – From [to fill] to [to fill].
Article 3 – Detour: Rue Duquesne → Avenue Georges Clemenceau → Rue de l'Harteloire → …`;

export const Detour: React.FC = () => {
	const frame = useCurrentFrame();
	const closed = interpolate(frame, [14, 34], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const route = interpolate(frame, [36, 92], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const order = useTyped(ORDER, 96, 78);
	const len = 190;
	return (
		<Stage glow="rgba(96,165,250,.13)">
			<Caption kicker="Detour and traffic order" title="Close the street. Route the traffic. Draft the order." sub="Shortest legal detour on OpenStreetMap, then Muse Spark drafts the mayor's order." top={250} width={580} left={90} />
			<Window x={720} y={70} w={1120} h={940} zoom={1.3}>
				<h2 style={{margin: '0 0 8px'}}>Approximate danger zone · along Avenue du Maréchal Foch, high danger</h2>
				<div style={{position: 'relative', width: 820, height: (820 * 258) / 549, borderRadius: 12, overflow: 'hidden'}}>
					<Img src={staticFile('img/detour-map.jpg')} style={{width: '100%', height: '100%', display: 'block', filter: 'saturate(0.2) brightness(0.9)'}} />
					<svg viewBox="0 0 549 258" style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
						<path d={CLOSED} stroke={C.clay} strokeWidth="7" strokeLinecap="round" fill="none" strokeDasharray={100} strokeDashoffset={100 * (1 - closed)} />
						<path d={ROUTE} stroke="#60a5fa" strokeWidth="9" strokeOpacity=".25" strokeLinecap="round" strokeLinejoin="round" fill="none" strokeDasharray={len} strokeDashoffset={len * (1 - route)} />
						<path d={ROUTE} stroke="#60a5fa" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill="none" strokeDasharray={len} strokeDashoffset={len * (1 - route)} />
						<circle cx="296" cy="166" r={6 + 2 * Math.sin(frame / 4)} fill="#fff" stroke={C.sev[4]} strokeWidth="3" />
					</svg>
				</div>
				<p style={{margin: '10px 0 6px', opacity: route}}>
					<b>Detour</b> (blue): 1,021 m via Rue Duquesne → Avenue Georges Clemenceau → Rue de l'Harteloire → Rue Bertrand du Guesclin → …
				</p>
				<p className="lb">Traffic order, AI draft to check before the mayor signs</p>
				<div className="ao" style={{marginTop: 4, minHeight: 210, fontSize: 13.5, lineHeight: 1.45}}>
					{order}
					<span style={{opacity: frame % 16 < 8 ? 1 : 0, color: C.clay}}>▍</span>
				</div>
			</Window>
		</Stage>
	);
};
