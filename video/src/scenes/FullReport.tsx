// Scene 6: "Generate full report" -> the live progress panel -> classification, regulatory path and the sourced cost.
import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Appear, C, Caption, Cursor, Stage, Step, useCount, useIn, Window} from '../lib';

const WX = 700, WY = 70, Z = 1.32;

const ROWS: [string, string, string, string, string, string][] = [
	['Temporary cold-mix patch, to make safe', 'temporary make-safe of the water-filled core, about 40 cm wide', '0.5 m²', '€26–€47', '€13–€24', "Prix de l'enrobé au m², Habitatpresto; BPU, commune de Prunelli-di-Fiumorbu, 2021"],
	['Planing (rabotage) of the old asphalt, 1 to 6 cm', 'surface broken to 8 cm over more than 3 cm', '2 m²', '€16', '€32', 'Grille des réfections de tranchées, Bourg-en-Bresse'],
	['Final hot-mix asphalt repair, under 10 m²', 'final repair squared around the cracked halo', '2 m²', '€79–€104', '€158–€208', 'BPU travaux, Régie des eaux Terre de Provence, 2022'],
	['Temporary road signage: set up and removal', 'works on a carriageway with a cycle lane', '1 lump sum', '€578', '€578', 'BPU travaux, Régie des eaux Terre de Provence, 2022'],
	['Temporary road signage: upkeep', 'make-safe and final repair', '3 days', '€29', '€87', 'BPU travaux, Régie des eaux Terre de Provence, 2022'],
];

const Progress: React.FC = () => {
	const frame = useCurrentFrame();
	const st = (a: number, b: number) => (frame < a ? 'wait' : frame < b ? 'run' : 'ok') as 'wait' | 'run' | 'ok';
	const secs = interpolate(frame, [22, 100], [0, 41.8], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<div className="pipe-card" style={{width: 560, margin: '30px auto 0', maxHeight: 'none', overflow: 'visible'}}>
			<div className="pipe-head">
				<div>
					<p className="pipe-k">Live AI</p>
					<h2>Full AI report</h2>
				</div>
				<span className="pipe-time">{secs.toFixed(1)} s</span>
			</div>
			<ol className="pipe-steps" style={{marginTop: 14}}>
				<Step state={st(22, 34)} who="InfraSight" text={frame >= 34 ? 'Ticket and history, photo, red zone, regulatory notes' : 'Gathering the ticket, photos and regulatory notes'} time="0.1 s" />
				<Step state={st(34, 84)} who="Muse Spark" text={frame >= 84 ? 'Severity 4/5 · Commune – Roads department · €868–928 from 5 priced lines' : 'Writing the full report'} time="40.6 s" />
				<Step state={st(84, 98)} who="OpenStreetMap" text={frame >= 98 ? 'Point, radius about 30 m' : 'Fitting the danger zone to the street'} time="41.8 s" />
			</ol>
			{frame >= 100 ? <p className="mu" style={{margin: '14px 0 0', fontSize: 12.5}}>Done in 41.8 s. AI results are drafts: check them before acting.</p> : null}
		</div>
	);
};

const Report: React.FC = () => {
	const frame = useCurrentFrame();
	const lo = useCount(868, 150, 230), hi = useCount(928, 150, 230);
	return (
		<div>
			<div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12}}>
				<Appear delay={112}>
					<div className="panel">
						<h2>Classification</h2>
						<p style={{margin: '4px 0'}}>
							<b>Type:</b> Roads
						</p>
						<p style={{margin: '4px 0'}}>
							<b>Severity:</b> <span className="sev" style={{background: C.sev[3]}}>4</span> Water-filled pothole on the carriageway next to a cycle lane, 30 m from a school.
						</p>
						<p style={{margin: '4px 0'}}>
							<b>Urgency:</b> under 48 hours. Make safe within 24 h.
						</p>
					</div>
				</Appear>
				<Appear delay={122}>
					<div className="panel">
						<h2>Regulatory path</h2>
						<p style={{margin: '4px 0'}}>
							<b>Procurement:</b> works under EUR 100,000 excl. VAT, no publicity or competition required <span style={{color: C.clay}}>(art. R2122-8 Code de la commande publique)</span>
						</p>
						<p style={{margin: '4px 0'}}>
							<b>Council vote:</b> Not required
						</p>
					</div>
				</Appear>
			</div>
			<Appear delay={136}>
				<div className="panel" style={{marginTop: 12}}>
					<h2>Cost estimate</h2>
					<p style={{margin: '0 0 6px'}}>
						<b>Estimate:</b> €{lo.toLocaleString('en')}–€{hi.toLocaleString('en')} excl. VAT
					</p>
					<table>
						<thead>
							<tr>
								<th>Work item</th>
								<th>Qty</th>
								<th>Rate</th>
								<th>Total</th>
							</tr>
						</thead>
						<tbody>
							{ROWS.map((r, i) => {
								const p = interpolate(frame, [146 + i * 14, 158 + i * 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
								return (
									<tr key={i} style={{opacity: p, transform: `translateX(${(1 - p) * 30}px)`}}>
										<td>
											{r[0]}
											<br />
											<span className="mu" style={{fontSize: 12}}>
												Source: <span style={{color: '#93b4ff', textDecoration: 'underline'}}>{r[5]}</span>
											</span>
										</td>
										<td style={{whiteSpace: 'nowrap'}}>{r[2]}</td>
										<td style={{whiteSpace: 'nowrap'}}>{r[3]}</td>
										<td style={{whiteSpace: 'nowrap'}}>{r[4]}</td>
									</tr>
								);
							})}
						</tbody>
					</table>
				</div>
			</Appear>
		</div>
	);
};

export const FullReport: React.FC = () => {
	const frame = useCurrentFrame();
	const progOut = interpolate(frame, [104, 114], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const progIn = useIn(16, 20);
	const btn = {x: WX + Z * (18 + 80), y: WY + Z * (18 + 92)};
	// slow push-in on the cost table once it is there
	const cam = interpolate(frame, [140, 300], [1, 1.06], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<Stage>
			<Caption kicker="AI report" title="A decision-ready report. Every euro sourced." sub="Muse Spark picks the work and the quantities. The server prices them from public rates." top={250} width={560} left={90} />
			<div style={{position: 'absolute', inset: 0, transform: `scale(${cam})`, transformOrigin: '75% 70%'}}>
				<Window x={WX} y={WY} w={1160} h={940} zoom={Z}>
					<div style={{display: 'flex', alignItems: 'baseline', gap: 10}}>
						<span className="mu" style={{fontFamily: 'Newsreader, Georgia, serif', fontSize: 16}}>IS-0042</span>
						<h1 style={{margin: 0, fontSize: 26}}>Pothole, Rue des Lilas</h1>
					</div>
					<div className="tabs" style={{margin: '10px 0 12px'}}>
						{['Overview', 'AI report', 'Danger and zone', 'Pipeline', 'Contacts', 'Audit log'].map((t, i) => (
							<button key={t} className={i === 1 ? 'on' : ''}>{t}</button>
						))}
					</div>
					{frame < 112 ? (
						<div className="row" style={{marginTop: 0}}>
							<button className="btn" style={{opacity: frame >= 20 ? 0.6 : 1}}>{frame >= 20 ? 'Analysing…' : 'Generate full report'}</button>
							<button className="btn alt">Download PDF report</button>
						</div>
					) : (
						<Report />
					)}
					{frame >= 14 && frame < 116 ? (
						<div style={{position: 'absolute', inset: 0, background: 'rgba(0,0,0,.55)', opacity: progOut * progIn}}>
							<div style={{transform: `scale(${0.95 + 0.05 * progIn})`}}>
								<Progress />
							</div>
						</div>
					) : null}
				</Window>
			</div>
			{frame < 30 ? <Cursor path={[{f: 0, x: 1500, y: 900}, {f: 12, x: btn.x, y: btn.y, click: true}, {f: 30, x: btn.x + 6, y: btn.y + 8}]} /> : null}
		</Stage>
	);
};
