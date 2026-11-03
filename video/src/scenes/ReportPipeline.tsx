// Scene 3: a citizen reports the smashed bus shelter, then watches the three Meta models work on it, live.
import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {Appear, C, Caption, Cursor, Stage, Step, useIn, useTyped, Window} from '../lib';

// window placement and zoom (screen px = WX + Z * (18 + css x))
const WX = 760, WY = 90, Z = 1.3;
const at = (x: number, y: number) => ({x: WX + Z * (18 + x), y: WY + Z * (18 + y)});

const Form: React.FC = () => {
	const frame = useCurrentFrame();
	const photo = useIn(22, 18);
	const addr = useTyped('8 rue dupleix', 34, 22);
	const picked = frame >= 66;
	const desc = useTyped('The bus shelter has been smashed: glass all over the pavement.', 72, 48);
	const sending = frame >= 112;
	return (
		<div style={{position: 'relative', height: 600}}>
			<h1 style={{margin: 0}}>Report a problem</h1>
			<p className="mu" style={{margin: '2px 0 0'}}>The AI reads your photo and text, sets the type and severity, and finds who is responsible.</p>
			<div style={{position: 'absolute', left: 0, top: 78, width: 330}}>
				<label className="f" style={{marginTop: 0}}>Photo (required)</label>
				<div style={{height: 220, borderRadius: 12, border: `1px dashed ${photo > 0.05 ? 'transparent' : 'rgba(255,255,255,.25)'}`, overflow: 'hidden', position: 'relative', display: 'grid', placeItems: 'center', color: C.muted}}>
					<span>Drop a photo</span>
					<Img src={staticFile('img/bus-photo.jpg')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: photo, transform: `scale(${1.15 - 0.15 * photo})`}} />
				</div>
			</div>
			<div style={{position: 'absolute', left: 356, top: 78, width: 350}}>
				<label className="f" style={{marginTop: 0}}>Address</label>
				<input readOnly value={picked ? '8 Rue Dupleix, Brest' : addr} style={{height: 38, borderColor: frame > 30 && frame < 66 ? C.clay : undefined}} />
				{frame >= 52 && !picked ? (
					<div className="sug" style={{display: 'flex'}}>
						<button className="sug-i" style={{borderColor: frame >= 60 ? C.clay : undefined}}>8 Rue Dupleix, Brest</button>
						<button className="sug-i">8 Rue Dupleix, Morlaix</button>
					</div>
				) : null}
				<p className="mu" style={{margin: '6px 0 0', color: picked ? '#86efac' : undefined}}>
					{picked ? '✓ On the map: 48.39345, -4.48210' : 'Type the address, then choose it in the list.'}
				</p>
				<label className="f">What is wrong?</label>
				<textarea readOnly rows={3} value={desc} style={{resize: 'none'}} />
				<div className="row">
					<button className="btn" style={{opacity: sending ? 0.6 : 1}}>{sending ? 'Sending…' : 'Send report'}</button>
				</div>
			</div>
		</div>
	);
};

const Pipeline: React.FC = () => {
	const frame = useCurrentFrame();
	const state = (start: number, end: number) => (frame < start ? 'wait' : frame < end ? 'run' : 'ok') as 'wait' | 'run' | 'ok';
	const secs = interpolate(frame, [124, 305], [0, 84.6], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const zone = interpolate(frame, [244, 256], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const prev = interpolate(frame, [304, 318], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const label = frame >= 304 ? 'Muse Image · after repair (illustration)' : frame >= 244 ? 'SAM 3.1 · damage outline' : 'Your photo';
	const done = frame >= 312;
	return (
		<div className="pipe-card" style={{width: 600, margin: '0 auto', maxHeight: 'none', overflow: 'visible', padding: 18}}>
			<div className="pipe-head">
				<div>
					<p className="pipe-k">Live AI analysis</p>
					<h2>Analysing your report</h2>
				</div>
				<span className="pipe-time">{secs.toFixed(1)} s</span>
			</div>
			<div className="pipe-photo" style={{margin: '12px 0', aspectRatio: '16 / 9'}}>
				<Img src={staticFile('img/bus-photo.jpg')} />
				<Img src={staticFile('img/bus-zone.jpg')} style={{opacity: zone}} />
				<Img src={staticFile('img/bus-preview.jpg')} style={{opacity: prev}} />
				<span className="pipe-lbl">{label}</span>
			</div>
			<ol className="pipe-steps">
				<Step state={state(130, 186)} who="Muse Spark" text={frame >= 186 ? 'Smashed bus shelter, Rue Dupleix · severity 4/5' : 'Reading your photo and your words…'} time="29.9 s" />
				<Step state={state(186, 246)} who="SAM 3.1" text={frame >= 246 ? 'Damage outlined in red, pixel by pixel' : frame >= 186 ? 'Outlining the damage on your photo…' : 'Waits for the triage'} time="59.4 s" />
				<Step state={state(246, 306)} who="Muse Image" text={frame >= 306 ? 'Here is your street once repaired (illustration)' : frame >= 246 ? 'Drawing the street repaired…' : 'Waits for the outline'} time="84.6 s" />
			</ol>
			{done ? (
				<Appear delay={312} y={10}>
					<p className="mu" style={{margin: '12px 0 0', fontSize: 12.5}}>Report IS-0050 registered. Every AI result is checked by the town hall's staff.</p>
				</Appear>
			) : null}
		</div>
	);
};

export const ReportPipeline: React.FC = () => {
	const frame = useCurrentFrame();
	const formOut = interpolate(frame, [116, 128], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const pipeIn = useIn(122, 20);
	// css positions of the form controls, measured on a rendered frame
	const send = at(413, 318), sug = at(470, 160), drop = at(160, 210), addr = at(532, 122), desc = at(532, 242);
	return (
		<Stage>
			<Caption kicker="Citizen report" title="One photo. Three Meta models. Live." sub="Pinned on the map, then analysed while the citizen watches." top={290} width={600} />
			<Window x={WX} y={WY} w={1060} h={900} zoom={Z}>
				<div style={{position: 'absolute', inset: 18, opacity: formOut}}>{frame < 130 ? <Form /> : null}</div>
				<div style={{position: 'absolute', inset: '8px 18px', opacity: pipeIn, transform: `scale(${0.96 + 0.04 * pipeIn})`}}>{frame >= 118 ? <Pipeline /> : null}</div>
			</Window>
			{frame < 122 ? (
				<Cursor
					path={[
						{f: 0, x: 1500, y: 980},
						{f: 16, x: drop.x, y: drop.y, click: true},
						{f: 30, x: addr.x, y: addr.y, click: true},
						{f: 54, x: sug.x, y: sug.y, click: true},
						{f: 70, x: desc.x, y: desc.y, click: true},
						{f: 104, x: send.x, y: send.y, click: true},
						{f: 122, x: send.x + 10, y: send.y + 10},
					]}
				/>
			) : null}
		</Stage>
	);
};
