"""Analyse the reference track: tempo, key, energy curve, brightness, rhythm feel, instruments, build-ups and drops."""
import json, sys
import numpy as np
import librosa

path, out = sys.argv[1], sys.argv[2]
y, sr = librosa.load(path, sr=22050, mono=True)
dur = len(y) / sr

# tempo and beats
onset = librosa.onset.onset_strength(y=y, sr=sr)
tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr)
tempo = float(np.atleast_1d(tempo)[0])
beat_t = librosa.frames_to_time(beats, sr=sr)
ibi = np.diff(beat_t)
# swing / steadiness: spread of inter-beat intervals
steadiness = float(np.std(ibi) / np.mean(ibi)) if len(ibi) > 2 else None

# key: Krumhansl-Schmuckler on the harmonic part's chroma
y_h, y_p = librosa.effects.hpss(y)
chroma = librosa.feature.chroma_cqt(y=y_h, sr=sr).mean(axis=1)
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
scores = []
for i in range(12):
    scores.append((np.corrcoef(chroma, np.roll(MAJ, i))[0, 1], NAMES[i], 'major'))
    scores.append((np.corrcoef(chroma, np.roll(MIN, i))[0, 1], NAMES[i], 'minor'))
scores.sort(reverse=True)
key = {'tonic': scores[0][1], 'mode': scores[0][2], 'confidence': round(float(scores[0][0]), 3),
       'runner_up': f'{scores[1][1]} {scores[1][2]} ({scores[1][0]:.3f})'}

# energy curve (RMS dB per second) and brightness
hop = 512
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
rms_db = librosa.amplitude_to_db(rms, ref=np.max)
t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
per_sec = [round(float(rms_db[(t >= s) & (t < s + 1)].mean()), 1) for s in range(int(np.ceil(dur)))]
cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
cent_sec = [round(float(cent[(t >= s) & (t < s + 1)].mean())) for s in range(int(np.ceil(dur)))]

# percussive vs harmonic share
perc_share = float(np.sum(y_p ** 2) / (np.sum(y_h ** 2) + np.sum(y_p ** 2)))

# frequency bands: what kind of instruments carry the track
S = np.abs(librosa.stft(y, n_fft=4096, hop_length=hop)) ** 2
f = librosa.fft_frequencies(sr=sr, n_fft=4096)
band = lambda lo, hi: float(S[(f >= lo) & (f < hi)].sum())
tot = band(20, 11025)
bands = {'sub 20-60 Hz': band(20, 60) / tot, 'bass 60-250 Hz': band(60, 250) / tot, 'low-mid 250-2k': band(250, 2000) / tot,
         'presence 2k-6k': band(2000, 6000) / tot, 'air 6k+': band(6000, 11025) / tot}
bands = {k: round(v * 100, 1) for k, v in bands.items()}

# build-ups and drops: smoothed energy, rises over 4 s, sudden jumps (drops) and sudden falls (breaks)
sm = np.convolve(per_sec, np.ones(3) / 3, mode='same')
events = []
for s in range(2, len(sm) - 1):
    jump = per_sec[s] - np.mean(per_sec[max(0, s - 3):s])
    if jump >= 4:
        events.append({'t': s, 'kind': 'drop / entry', 'jump_db': round(float(jump), 1)})
    elif jump <= -5:
        events.append({'t': s, 'kind': 'break', 'jump_db': round(float(jump), 1)})
rises = [{'from': s, 'to': s + 4, 'rise_db': round(float(sm[s + 4] - sm[s]), 1)}
         for s in range(0, len(sm) - 5) if sm[s + 4] - sm[s] >= 4]

# sections from a self-similarity novelty curve
mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=13)
bounds = librosa.segment.agglomerative(mfcc, k=6)
sections = [round(float(x), 1) for x in librosa.frames_to_time(bounds, sr=sr, hop_length=hop)]

mood = ('dark, tense' if key['mode'] == 'minor' else 'bright, positive') + \
       (', driving' if tempo >= 115 else ', relaxed' if tempo < 95 else ', mid-tempo') + \
       (', punchy' if perc_share > 0.4 else ', smooth')
res = {'duration_s': round(dur, 2), 'tempo_bpm': round(tempo, 1), 'beat_steadiness': steadiness, 'key': key,
       'mood': mood, 'percussive_share': round(perc_share, 3), 'bands_percent': bands,
       'energy_db_per_second': per_sec, 'brightness_hz_per_second': cent_sec,
       'energy_events': events, 'build_ups': rises, 'section_starts_s': sections,
       'first_beat_s': round(float(beat_t[0]), 3) if len(beat_t) else None}
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('energy_db_per_second', 'brightness_hz_per_second')}, indent=1))
print('energy dB/s:', per_sec)
