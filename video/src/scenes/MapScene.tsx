// Scene 4: the staff map, with incidents pulsing, AI danger zones, detours and hotspots.
import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {Appear, C, Caption, Stage, useIn} from '../lib';

// incident dots in the map image (1164 x 746 px)
const DOTS = [
	{x: 573, y: 334, c: C.sev[4]},
	{x: 568, y: 384, c: C.sev[3]},
	{x: 628, y: 338, c: C.sev[3]},
	{x: 678, y: 364, c: C.sev[2]},
	{x: 595, y: 262, c: C.sev[4]},
];

export const MapScene: React.FC = () => {
	const frame = useCurrentFrame();
	const W = 1164, H = 746, x = 700, y = 150, w = 1120, h = 718;
	const k = w / W;
	const zoom = interpolate(frame, [0, 180], [1, 1.35]);
	const pop = useIn(70, 14);
	return (
		<Stage>
			<Caption kicker="Staff map" title="Every danger, on one map." sub="Severity colours, AI danger zones, detours and hotspots." top={300} width={560} />
			<Appear delay={0} y={50} style={{position: 'absolute', left: x, top: y, width: w, height: h}}>
				<div style={{position: 'absolute', inset: 0, borderRadius: 26, overflow: 'hidden', border: '1px solid rgba(255,255,255,.1)', boxShadow: '0 40px 120px rgba(0,0,0,.7)'}}>
					<div style={{position: 'absolute', inset: 0, transform: `scale(${zoom})`, transformOrigin: `${(600 / W) * 100}% ${(350 / H) * 100}%`}}>
						<Img src={staticFile('img/map.jpg')} style={{width: w, height: h, objectFit: 'cover', display: 'block'}} />
						{DOTS.map((d, i) => {
							const t = (frame - i * 7) % 40;
							return (
								<div key={i} style={{position: 'absolute', left: d.x * k, top: d.y * k}}>
									<div style={{position: 'absolute', left: -18, top: -18, width: 36, height: 36, borderRadius: '50%', border: `2px solid ${d.c}`, opacity: t < 0 ? 0 : 1 - t / 40, transform: `scale(${0.4 + t / 25})`}} />
								</div>
							);
						})}
					</div>
					<div
						style={{
							position: 'absolute',
							left: 470,
							top: 170,
							width: 330,
							opacity: pop,
							transform: `translateY(${(1 - pop) * 20}px) scale(${0.9 + 0.1 * pop})`,
							background: '#121214',
							border: '1px solid rgba(255,255,255,.12)',
							borderRadius: 14,
							padding: 14,
							boxShadow: '0 20px 50px rgba(0,0,0,.6)',
						}}
					>
						<div style={{display: 'flex', gap: 12}}>
							<Img src={staticFile('img/bus-zone.jpg')} style={{width: 92, height: 70, objectFit: 'cover', borderRadius: 8}} />
							<div>
								<div style={{fontWeight: 700, fontSize: 18}}>IS-0050: Smashed bus shelter</div>
								<div style={{color: C.muted, fontSize: 15, marginTop: 4}}>
									Severity <b style={{color: C.sev[3]}}>8 / 10</b> · Rue Dupleix
								</div>
							</div>
						</div>
					</div>
				</div>
			</Appear>
			<div style={{position: 'absolute', left: x, top: y + h + 26, display: 'flex', gap: 14}}>
				{[
					['Incidents by severity', C.sev[3]],
					['AI danger zones', C.sev[4]],
					['Detours', '#60a5fa'],
					['Hotspots', '#a855f7'],
				].map(([t, c], i) => (
					<Appear key={t} delay={20 + i * 8} y={14}>
						<div style={{display: 'flex', alignItems: 'center', gap: 10, padding: '10px 18px', borderRadius: 999, background: '#111113', border: '1px solid rgba(255,255,255,.1)', fontSize: 22}}>
							<span style={{width: 14, height: 14, borderRadius: '50%', background: c}} />
							{t}
						</div>
					</Appear>
				))}
			</div>
		</Stage>
	);
};
