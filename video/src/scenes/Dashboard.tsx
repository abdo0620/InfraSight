// Scene 12: the dashboard. Figures count up, the priority matrix fills, the weekly brief writes itself, a hotspot appears.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {Appear, C, Caption, Stage, useCount, useIn, useTyped, Window} from '../lib';

const BRIEF =
	'This week: 4 new reports, 5 open, 4 with severity 4 or 5. Act first on the water main leak, Place de la Liberté (access blocked), and the sunken manhole cover on RD 14, now past its deadline.';
// priority matrix: [severity row, urgency column, count]
const CELLS: [number, number, number][] = [[5, 5, 1], [4, 4, 2], [4, 5, 1], [3, 2, 1]];

export const Dashboard: React.FC = () => {
	const frame = useCurrentFrame();
	const k = [useCount(5, 6, 36), useCount(4, 6, 36), useCount(1, 6, 36), useCount(1, 6, 36), useCount(21148, 6, 46)];
	const brief = useTyped(BRIEF, 50, 70);
	const hot = useIn(120, 16);
	return (
		<Stage>
			<Caption kicker="Dashboard" title="Priorities, budget and a weekly brief." sub="Written by Muse Spark for the elected officials." top={300} width={540} />
			<Window x={700} y={120} w={1140} h={820} zoom={1.38}>
				<h1 style={{margin: '0 0 10px', fontSize: 28}}>Dashboard</h1>
				<div className="panel">
					<div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
						<h2 style={{margin: 0}}>Weekly brief</h2>
						<button className="btn">Write this week's brief</button>
					</div>
					<p style={{margin: '10px 0 0', minHeight: 62}}>{brief}</p>
				</div>
				<div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginTop: 10}}>
					{[
						[k[0], 'Open tickets'],
						[k[1], 'Severity 4 or 5'],
						[k[2], 'Past deadline'],
						[k[3], 'Awaiting decision'],
						['€' + k[4].toLocaleString('en'), 'Committed estimate'],
					].map(([v, l]) => (
						<div key={l as string} className="panel kpi">
							<b>{v}</b>
							<span>{l}</span>
						</div>
					))}
				</div>
				<div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10}}>
					<div className="panel">
						<h2>Priority matrix</h2>
						<div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 34px)', gap: 4}}>
							{[5, 4, 3, 2, 1].flatMap((sev) =>
								[1, 2, 3, 4, 5].map((urg) => {
									const c = CELLS.find((x) => x[0] === sev && x[1] === urg);
									const d = c ? 30 + CELLS.indexOf(c) * 8 : 0;
									return (
										<Appear key={`${sev}${urg}`} delay={d} scale={c ? 0.3 : 1} y={0}>
											<div style={{height: 30, borderRadius: 5, background: c ? C.sev[sev - 1] : '#161618', color: '#111', fontWeight: 700, display: 'grid', placeItems: 'center'}}>{c ? c[2] : ''}</div>
										</Appear>
									);
								}),
							)}
						</div>
						<p className="mu" style={{margin: '6px 0 0', fontSize: 12}}>Rows: severity. Columns: urgency.</p>
					</div>
					<div className="panel" style={{opacity: hot, transform: `translateY(${(1 - hot) * 20}px)`}}>
						<h2>Hotspot · AI forecast</h2>
						<div style={{display: 'flex', gap: 12, alignItems: 'center'}}>
							<div style={{width: 56, height: 56, borderRadius: '50%', border: '3px dashed #a855f7', flex: 'none'}} />
							<div>
								<b>Rue Victor Hugo</b>: 3 reports in 12 months.
								<div className="mu">Tree roots lifting the pavement: plan a root barrier before winter.</div>
							</div>
						</div>
					</div>
				</div>
			</Window>
		</Stage>
	);
};
