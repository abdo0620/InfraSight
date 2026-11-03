// Scene 5: the ticket. The before / after slider sweeps over the bus shelter; the photo, SAM 3.1 outline and Muse Image
// repair preview line up next to it.
import React from 'react';
import {Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {Appear, C, Caption, Cursor, Stage, Window} from '../lib';

const WX = 740, WY = 90, Z = 1.45;
// slider keyframes: [frame, position %]; the cursor holds the knob along the same path
const KEYS: [number, number][] = [[20, 96], [70, 6], [120, 92], [170, 30], [210, 52]];
// the slider is 520 css px wide at the window's padding; on screen it is scaled by Z
const knobX = (p: number) => WX + Z * (18 + (520 * p) / 100);
const ky = WY + Z * (18 + 150 + 173);

export const TicketSlider: React.FC = () => {
	const frame = useCurrentFrame();
	const pos = interpolate(frame, KEYS.map((k) => k[0]), KEYS.map((k) => k[1]), {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.bezier(0.6, 0, 0.2, 1),
	});
	const figs = [
		['bus-photo.jpg', 'Photo', 'As reported'],
		['bus-zone.jpg', 'Damage zone', 'Outlined by SAM 3.1'],
		['bus-preview.jpg', 'After repair · AI preview', 'Illustration, not a photo'],
	];
	return (
		<Stage>
			<Caption kicker="The ticket" title="See the street repaired before work starts." sub="SAM 3.1 outlines the damage. Muse Image draws the repair." top={280} width={580} />
			<Window x={WX} y={WY} w={1080} h={900} zoom={Z}>
				<div style={{display: 'flex', alignItems: 'center', gap: 10}}>
					<Img src={staticFile('img/bus-photo.jpg')} style={{width: 44, height: 34, objectFit: 'cover', borderRadius: 4}} />
					<span className="mu" style={{fontFamily: 'Newsreader, Georgia, serif', fontSize: 16}}>IS-0050</span>
					<h1 style={{margin: 0, fontSize: 26}}>Smashed bus shelter, Rue Dupleix</h1>
				</div>
				<div style={{display: 'flex', gap: 6, marginTop: 8}}>
					<span className="sev" style={{background: C.sev[3]}}>4</span>
					<span className="tag">Other</span>
					<span className="tag">Commune (municipal domain)</span>
					<span className="tag">Intake and registration</span>
				</div>
				<div className="tabs" style={{margin: '10px 0 12px'}}>
					{['Overview', 'AI report', 'Danger and zone', 'Pipeline', 'Contacts', 'Audit log'].map((t, i) => (
						<button key={t} className={i === 0 ? 'on' : ''}>{t}</button>
					))}
				</div>
				<div style={{display: 'flex', gap: 16}}>
					<div style={{width: 520}}>
						<div className="cmp" style={{['--pos' as string]: `${pos}%`}}>
							<Img src={staticFile('img/bus-preview.jpg')} />
							<Img className="cmp-before" src={staticFile('img/bus-photo.jpg')} />
							<span className="cmp-line">
								<span className="cmp-knob" />
							</span>
							<span className="cmp-tag cmp-l">Before</span>
							<span className="cmp-tag cmp-r">After · AI preview</span>
						</div>
						<p className="mu cmp-note">Drag to compare the photo with Muse Image's illustration of the repaired street.</p>
					</div>
					<div style={{width: 160, display: 'grid', gap: 8}}>
						{figs.map(([f, b, s], i) => (
							<Appear key={f} delay={40 + i * 14} x={30} y={0}>
								<figure className="vg" style={{margin: 0, display: 'block'}}>
									<Img src={staticFile('img/' + f)} style={{width: '100%', aspectRatio: '4/3', objectFit: 'cover', borderRadius: 10, border: '1px solid rgba(255,255,255,.08)', display: 'block'}} />
									<figcaption style={{fontSize: 11.5, color: C.muted, marginTop: 4}}>
										<b style={{color: C.text, fontWeight: 500}}>{b}</b>
										<br />
										{s}
									</figcaption>
								</figure>
							</Appear>
						))}
					</div>
				</div>
			</Window>
			<Cursor
				path={[
					{f: 0, x: 1700, y: 1000},
					...KEYS.map(([f, p], i) => ({f, x: knobX(p), y: ky, click: i === 0})),
				]}
			/>
		</Stage>
	);
};
