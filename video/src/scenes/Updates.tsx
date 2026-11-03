// Scene 11: citizens get each update written by the AI in their own language.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {Appear, C, Caption, Stage} from '../lib';

const MSGS: [string, string, boolean?][] = [
	['English', 'Your report about the bus shelter on Rue Dupleix was received. The roads team will make it safe today.'],
	['Français', "Votre signalement de l'abribus rue Dupleix a bien été reçu. L'équipe voirie sécurise la zone aujourd'hui."],
	['Español', 'Hemos recibido tu aviso sobre la marquesina de la calle Dupleix. El equipo municipal la asegura hoy.'],
	['العربية', 'تم استلام بلاغك عن موقف الحافلات في شارع دوبليكس. سيؤمّن فريق الطرق المكان اليوم.', true],
];
const LANGS = ['English', 'Français', 'Brezhoneg', 'Español', 'Português', 'العربية', 'Türkçe', 'Deutsch', 'Italiano'];

export const Updates: React.FC = () => {
	useCurrentFrame();
	return (
		<Stage>
			<Caption kicker="Citizen updates" title="Every citizen hears back, in their language." sub="9 languages, at every step of the repair." top={300} width={600} />
			<div style={{position: 'absolute', left: 820, top: 110, width: 1000, display: 'grid', gap: 18}}>
				{MSGS.map(([lang, text, rtl], i) => (
					<Appear key={lang} delay={6 + i * 18} x={60} y={0}>
						<div style={{display: 'flex', flexDirection: rtl ? 'row-reverse' : 'row', gap: 16, alignItems: 'flex-start'}}>
							<span style={{flex: 'none', padding: '8px 14px', borderRadius: 999, background: C.claySoft, color: '#f7c3ae', fontSize: 20, fontWeight: 700}}>{lang}</span>
							<div dir={rtl ? 'rtl' : 'ltr'} style={{background: '#121214', border: '1px solid rgba(255,255,255,.1)', borderRadius: 20, padding: '18px 22px', fontSize: 27, lineHeight: 1.35}}>
								{text}
							</div>
						</div>
					</Appear>
				))}
				<Appear delay={86} y={20}>
					<div style={{display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 10}}>
						{LANGS.map((l) => (
							<span key={l} style={{padding: '6px 14px', borderRadius: 999, border: '1px solid rgba(255,255,255,.14)', color: C.muted, fontSize: 19}}>
								{l}
							</span>
						))}
					</div>
				</Appear>
			</div>
		</Stage>
	);
};
