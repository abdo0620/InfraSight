// The trailer's sound: the music track (versions 2 and 3), ducked under the effects, and every effect in its own
// <Sequence>, at the frame where its event happens on screen.
import React, {useMemo} from 'react';
import {Audio, Sequence, staticFile} from 'remotion';
import {SCENE_START, TOTAL} from '../Trailer';
import {duckCurve, placeCues} from './cues';

const MUSIC: Record<number, string> = {2: 'music/generated.wav', 3: 'music/inspired.wav', 4: 'music/streets.wav'};

export const Soundtrack: React.FC<{version: 1 | 2 | 3 | 4}> = ({version}) => {
	const cues = useMemo(() => placeCues(SCENE_START), []);
	const duck = useMemo(() => duckCurve(cues, TOTAL), [cues]);
	return (
		<>
			{MUSIC[version] ? (
				<Sequence from={0} durationInFrames={TOTAL} layout="none" name="Music">
					<Audio src={staticFile(MUSIC[version])} volume={(f) => duck[Math.min(f, TOTAL - 1)]} />
				</Sequence>
			) : null}
			{cues.map((c, i) => (
				<Sequence key={i} from={c.from} durationInFrames={c.frames} layout="none" name={`sfx ${c.sfx}`}>
					<Audio src={staticFile(`sfx/${c.sfx}.wav`)} volume={c.volume} />
				</Sequence>
			))}
		</>
	);
};
