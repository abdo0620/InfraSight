// Scene 13: the incident report, as a PDF: the real pages fan out.
import React from 'react';
import {Img, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Caption, Stage} from '../lib';

export const PdfReport: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const pages = [1, 2, 3, 4];
	return (
		<Stage>
			<Caption kicker="PDF report" title="One click. The whole case, on paper." sub="Images, sources, cost, stages, detour and traffic order." top={320} width={540} />
			<div style={{position: 'absolute', left: 1290, top: 560}}>
				{pages.map((p, i) => {
					const s = spring({frame: frame - 6 - i * 6, fps, config: {damping: 15, mass: 0.8}});
					const spread = i - 1.5;
					return (
						<Img
							key={p}
							src={staticFile(`img/pdf-${p}.jpg`)}
							style={{
								position: 'absolute',
								width: 400,
								maxWidth: 'none', // the app's stylesheet caps images at their container's width (0 here)
								left: -200,
								top: -283,
								borderRadius: 6,
								boxShadow: '0 30px 70px rgba(0,0,0,.6)',
								transform: `translateX(${spread * 230 * s}px) translateY(${Math.abs(spread) * 26 * s + (1 - s) * 200}px) rotate(${spread * 6 * s}deg)`,
								opacity: Math.min(1, s * 2),
								zIndex: 10 - Math.abs(Math.round(spread * 2)),
							}}
						/>
					);
				})}
			</div>
		</Stage>
	);
};
