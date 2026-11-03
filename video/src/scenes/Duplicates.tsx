// Scene 8: two citizens report the same pothole; Muse Spark sees it is the same problem and merges the reports.
import React from 'react';
import {Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Appear, C, Caption, Stage} from '../lib';

const Card: React.FC<{img: string; flip?: boolean; who: string; text: string; style?: React.CSSProperties}> = ({img, flip, who, text, style}) => (
	<div style={{position: 'absolute', width: 400, background: '#0f0f11', border: '1px solid rgba(255,255,255,.1)', borderRadius: 22, padding: 16, boxShadow: '0 30px 80px rgba(0,0,0,.6)', ...style}}>
		<Img src={staticFile('img/' + img)} style={{width: '100%', height: 230, objectFit: 'cover', borderRadius: 14, transform: flip ? 'scaleX(-1)' : undefined}} />
		<div style={{fontSize: 22, fontWeight: 700, marginTop: 12}}>{who}</div>
		<div style={{fontSize: 19, color: C.muted, marginTop: 4}}>{text}</div>
	</div>
);

export const Duplicates: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const merge = spring({frame: frame - 52, fps, config: {damping: 16}});
	const gone = interpolate(frame, [70, 80], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const cx = 1290;
	return (
		<Stage>
			<Caption kicker="Duplicate merging" title="Same problem twice? One ticket." sub="Within 80 m, Muse Spark checks it is the same problem." top={320} width={560} />
			<div style={{opacity: gone}}>
				<Appear delay={2} x={-80} y={0}>
					<Card img="pothole-photo.jpg" who="Report from Léa · 08:12" text="Huge pothole by the school, full of water." style={{left: interpolate(merge, [0, 1], [800, cx - 200]), top: 230, transform: `rotate(${-4 * (1 - merge)}deg)`}} />
				</Appear>
				<Appear delay={10} x={80} y={0}>
					<Card img="pothole-photo.jpg" flip who="Report from Karim · 09:40" text="A cyclist nearly fell in a hole on Rue des Lilas." style={{left: interpolate(merge, [0, 1], [1360, cx - 200]), top: 290, transform: `rotate(${5 * (1 - merge)}deg)`}} />
				</Appear>
			</div>
			{frame >= 72 ? (
				<Appear delay={72} scale={0.85} y={0} style={{position: 'absolute', left: cx - 260, top: 220}}>
					<div style={{width: 520, background: '#0f0f11', border: `2px solid ${C.clay}`, borderRadius: 24, padding: 18, boxShadow: '0 30px 90px rgba(217,119,87,.25)'}}>
						<Img src={staticFile('img/pothole-zone.jpg')} style={{width: '100%', height: 270, objectFit: 'cover', borderRadius: 14}} />
						<div style={{fontSize: 26, fontWeight: 700, marginTop: 14}}>IS-0042 · Pothole, Rue des Lilas</div>
						<div style={{display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap'}}>
							<span style={{padding: '6px 14px', borderRadius: 999, background: C.claySoft, color: '#f7c3ae', fontSize: 19, fontWeight: 600}}>2 citizens follow this ticket</span>
							<span style={{padding: '6px 14px', borderRadius: 999, background: '#161618', color: C.muted, fontSize: 19}}>12 m apart · same problem</span>
						</div>
					</div>
				</Appear>
			) : null}
		</Stage>
	);
};
