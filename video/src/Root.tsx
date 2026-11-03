import React from 'react';
import {Composition} from 'remotion';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadNewsreader} from '@remotion/google-fonts/Newsreader';
// the app's own stylesheet: panels, buttons, the live AI panel, the before / after slider look exactly as in the app
import '../../frontend/css/styles.css';
import {TOTAL, Trailer, TrailerProps} from './Trailer';
import {LogoSting, STING_FRAMES} from './scenes/LogoSting';
import {SHORT_TOTAL, TrailerShort} from './TrailerShort';
import {FINAL_TOTAL, FinalVideo} from './FinalVideo';

loadInter('normal', {weights: ['400', '500', '600', '700', '800'], subsets: ['latin', 'latin-ext']});
loadNewsreader('normal', {weights: ['400', '500'], subsets: ['latin', 'latin-ext']});

// --props='{"version":1|2|3|4}' picks the soundtrack (see Trailer.tsx); 0 = silent
export const RemotionRoot: React.FC = () => (
	<>
		<Composition
			id="Trailer"
			component={Trailer}
			durationInFrames={TOTAL}
			fps={30}
			width={1920}
			height={1080}
			defaultProps={{version: 2} as TrailerProps}
		/>
		{/* short logo transition between the trailer and the live demo recording */}
		<Composition id="LogoSting" component={LogoSting} durationInFrames={STING_FRAMES} fps={30} width={1920} height={1080} />
		{/* the final film: short trailer, logo transition, live demo recording (public/live/live_demo.mp4) */}
		<Composition id="TrailerShort" component={TrailerShort} durationInFrames={SHORT_TOTAL} fps={30} width={1920} height={1080} />
		<Composition id="FinalVideo" component={FinalVideo} durationInFrames={FINAL_TOTAL} fps={30} width={1920} height={1080} />
	</>
);
