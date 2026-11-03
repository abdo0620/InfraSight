// Shared animation helpers and small pieces used by every scene.
import React from 'react';
import {Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export const C = {
	bg: '#000',
	panel: '#0b0b0d',
	panel2: '#161618',
	line: 'rgba(255,255,255,.08)',
	text: '#f4f4f5',
	muted: '#9a9aa3',
	clay: '#d97757',
	claySoft: 'rgba(217,119,87,.14)',
	green: '#16a34a',
	sev: ['#6b7a8a', '#9a8f5c', '#c9952c', '#d97706', '#ef4444'],
	meta: '#0467DF',
};
export const SERIF = 'Newsreader, Georgia, serif';
export const SANS = 'Inter, system-ui, sans-serif';

/** 0 -> 1 with a soft spring, starting at `delay` frames. */
export const useIn = (delay = 0, damping = 200, durationInFrames?: number) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return spring({frame: frame - delay, fps, config: {damping}, durationInFrames});
};

/** Linear 0 -> 1 between two frames, eased. */
export const useProgress = (from: number, to: number) => {
	const frame = useCurrentFrame();
	return interpolate(frame, [from, to], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.bezier(0.45, 0, 0.2, 1),
	});
};

/** Text typed from `start`, at `cps` characters per second. */
export const useTyped = (text: string, start: number, cps = 40) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const n = Math.max(0, Math.floor(((frame - start) / fps) * cps));
	return text.slice(0, n);
};

/** Fades and lifts its children in at `delay`. */
export const Appear: React.FC<{delay?: number; y?: number; x?: number; scale?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({
	delay = 0,
	y = 24,
	x = 0,
	scale = 1,
	style,
	children,
}) => {
	const p = useIn(delay);
	return (
		<div
			style={{
				opacity: p,
				transform: `translate(${(1 - p) * x}px, ${(1 - p) * y}px) scale(${scale + (1 - scale) * p})`,
				...style,
			}}
		>
			{children}
		</div>
	);
};

/** Scene background: black with a faint street grid and a clay glow. */
export const Stage: React.FC<{children: React.ReactNode; glow?: string}> = ({children, glow = 'rgba(217,119,87,.16)'}) => {
	const frame = useCurrentFrame();
	return (
		<div style={{position: 'absolute', inset: 0, background: C.bg, overflow: 'hidden', fontFamily: SANS, color: C.text}}>
			<div
				style={{
					position: 'absolute',
					inset: -60,
					backgroundImage:
						'linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px)',
					backgroundSize: '80px 80px',
					transform: `translate(${(frame * 0.3) % 80}px, ${(frame * 0.15) % 80}px)`,
				}}
			/>
			<div style={{position: 'absolute', inset: 0, background: `radial-gradient(ellipse at 75% 40%, ${glow} 0%, transparent 55%)`}} />
			<div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,.85) 100%)'}} />
			<div style={{position: 'absolute', inset: 0}}>{children}</div>
		</div>
	);
};

/** The left-hand caption of a feature scene: kicker, headline (words spring in), and a line under it. */
export const Caption: React.FC<{kicker: string; title: string; sub?: string; width?: number; top?: number; left?: number}> = ({
	kicker,
	title,
	sub,
	width = 600,
	top = 300,
	left = 110,
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const words = title.split(' ');
	return (
		<div style={{position: 'absolute', left, top, width}}>
			<Appear delay={2} y={12}>
				<div style={{fontSize: 26, fontWeight: 700, letterSpacing: '.16em', textTransform: 'uppercase', color: C.clay}}>{kicker}</div>
			</Appear>
			<div style={{fontFamily: SERIF, fontSize: 76, lineHeight: 1.04, fontWeight: 500, letterSpacing: '-.02em', marginTop: 18}}>
				{words.map((w, i) => {
					const p = spring({frame: frame - 6 - i * 3, fps, config: {damping: 18, mass: 0.6}});
					return (
						<span key={i} style={{display: 'inline-block', marginRight: 18, opacity: Math.min(1, p * 1.4), transform: `translateY(${(1 - p) * 40}px)`}}>
							{w}
						</span>
					);
				})}
			</div>
			{sub ? (
				<Appear delay={14 + words.length * 3} y={14}>
					<div style={{fontSize: 32, lineHeight: 1.35, color: C.muted, marginTop: 24}}>{sub}</div>
				</Appear>
			) : null}
		</div>
	);
};

/** Mouse pointer that glides between points and clicks. */
export const Cursor: React.FC<{path: {f: number; x: number; y: number; click?: boolean}[]}> = ({path}) => {
	const frame = useCurrentFrame();
	const fs = path.map((p) => p.f);
	const ease = Easing.bezier(0.6, 0, 0.2, 1);
	const x = interpolate(frame, fs, path.map((p) => p.x), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
	const y = interpolate(frame, fs, path.map((p) => p.y), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
	const clicks = path.filter((p) => p.click).map((p) => p.f + 6);
	const last = clicks.filter((c) => c <= frame).pop();
	const since = last === undefined ? 99 : frame - last;
	const press = since < 6 ? 0.85 : 1;
	return (
		<div style={{position: 'absolute', left: 0, top: 0, transform: `translate(${x}px, ${y}px)`, zIndex: 50, pointerEvents: 'none'}}>
			{since < 18 ? (
				<div
					style={{
						position: 'absolute',
						left: -26,
						top: -26,
						width: 52,
						height: 52,
						borderRadius: '50%',
						border: `3px solid ${C.clay}`,
						opacity: 1 - since / 18,
						transform: `scale(${0.4 + since / 12})`,
					}}
				/>
			) : null}
			<svg width="34" height="40" viewBox="0 0 17 20" style={{transform: `scale(${press})`, transformOrigin: '0 0', filter: 'drop-shadow(0 3px 6px rgba(0,0,0,.6))'}}>
				<path d="M1 1 L1 16 L5 12 L8 19 L11 18 L8 11 L14 11 Z" fill="#fff" stroke="#111" strokeWidth="1.2" strokeLinejoin="round" />
			</svg>
		</div>
	);
};

/** The InfraSight logo: a radar over the street grid, with a turning beam. */
export const Radar: React.FC<{size: number; spin?: number; draw?: number; blip?: boolean}> = ({size, spin = 0, draw = 1, blip = true}) => {
	const circ = 2 * Math.PI * 27;
	const blipOn = blip && (((spin % 360) + 360) % 360) > 30 && (((spin % 360) + 360) % 360) < 120;
	return (
		<svg viewBox="0 0 64 64" width={size} height={size} fill="none">
			<circle cx="32" cy="32" r="27" stroke={C.clay} strokeWidth="3" strokeDasharray={circ} strokeDashoffset={circ * (1 - draw)} transform="rotate(-90 32 32)" />
			<path d="M8 36H56M30 6 34 58" stroke={C.clay} strokeWidth="2" strokeOpacity={0.35 * draw} />
			<path d="M32 32V5A27 27 0 0 1 55.4 18.5Z" fill={C.clay} fillOpacity={0.45 * draw} transform={`rotate(${spin} 32 32)`} />
			<circle cx="32" cy="32" r="3.5" fill={C.clay} opacity={draw} />
			<circle cx="44" cy="22" r="3.5" fill="#f4f4f5" opacity={blipOn ? 1 : 0} />
		</svg>
	);
};

/** Spinner of a running AI step (the app's .pi ring), driven by the frame instead of a CSS animation. */
export const Spin: React.FC = () => {
	const frame = useCurrentFrame();
	return (
		<span
			className="pi"
			style={{borderColor: C.clay, borderTopColor: 'transparent', transform: `rotate(${frame * 14}deg)`}}
		/>
	);
};

/** One step of the app's live AI panel (.pipe-steps li). state: wait | run | ok */
export const Step: React.FC<{state: 'wait' | 'run' | 'ok'; who: string; text: string; time?: string; big?: boolean}> = ({state, who, text, time}) => (
	<li className={state}>
		{state === 'run' ? <Spin /> : <span className="pi" />}
		<div>
			<b>{who}</b>
			<span className="pr">{text}</span>
		</div>
		<span className="pt">{state === 'ok' ? time : ''}</span>
	</li>
);

/** Counts up to `to` between two frames. */
export const useCount = (to: number, from: number, until: number) => {
	const p = useProgress(from, until);
	return Math.round(to * p);
};

/** A zoomed window on the app: the real UI at `zoom` times its size, so it stays readable on a phone. */
export const Window: React.FC<{x: number; y: number; w: number; h: number; zoom?: number; delay?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({
	x,
	y,
	w,
	h,
	zoom = 1.5,
	delay = 0,
	children,
	style,
}) => {
	const p = useIn(delay, 20);
	return (
		<div
			style={{
				position: 'absolute',
				left: x,
				top: y,
				width: w,
				height: h,
				borderRadius: 26,
				overflow: 'hidden',
				background: '#050506',
				border: '1px solid rgba(255,255,255,.1)',
				boxShadow: '0 40px 120px rgba(0,0,0,.7), 0 0 0 1px rgba(217,119,87,.08)',
				opacity: Math.min(1, p * 1.5),
				transform: `translateY(${(1 - p) * 60}px) scale(${0.94 + 0.06 * p})`,
				...style,
			}}
		>
			<div style={{width: w / zoom, height: h / zoom, transform: `scale(${zoom})`, transformOrigin: '0 0', padding: 18, boxSizing: 'border-box', fontSize: 14, lineHeight: 1.45}}>
				{children}
			</div>
		</div>
	);
};
