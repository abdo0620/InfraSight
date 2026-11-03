"""Composes the background tracks, exactly the length of the trailer, on the trailer's own scene timings
(src/timeline.json). Run from video/: python audio/make_music.py [generated|inspired|streets ...]
  public/music/generated.wav  version 2: upbeat electronic, ~120 BPM, beat, bass, pad, arpeggio
  public/music/inspired.wav   version 3: original track shaped by the analysis of the reference music (see below)
  public/music/streets.wav    version 4: laid-back cinematic hip-hop beat, ~93 BPM"""
import json
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from synth import (SR, Track, bell, clap, crash, hat, hp, hz, kick, lp, pad, pluck, reverb, rim, riser, snare_roll,
                   soft_kick, sub, to_rms)

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "src" / "timeline.json").read_text())
FPS, T = TL["fps"], TL["transition"]

# when each scene starts in the finished video, in seconds (same rule as Trailer.tsx)
START, at = {}, 0
for s in TL["scenes"]:
    START[s["name"]] = at / FPS
    at += s["frames"] - (0 if s["into_next"] == "cut" else T)
LENGTH = at / FPS                     # 95.4 s
CUTS = [START[s["name"]] for s in TL["scenes"][1:]]


def save(track, name, rms_db=-20.0):
    x = to_rms(track.buf, rms_db)
    peak = np.max(np.abs(x))
    if peak > 0.89:                   # keep 1 dB of headroom: soft-limit the rare peaks instead of clipping
        x = np.tanh(x / 0.89) * 0.89
    out = ROOT / "public" / "music" / f"{name}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(out, SR, (x * 32767).astype(np.int16))
    print(f"{out.name}: {len(x) / SR:.3f} s, peak {20 * np.log10(np.max(np.abs(x))):.1f} dBFS")


def end_fade(track, seconds):
    n = int(seconds * SR)
    track.buf[-n:] *= np.linspace(1, 0, n)[:, None] ** 1.5


# ---------------------------------------------------------------------------------------------------------------
# Version 2: upbeat electronic. The drop lands on the citizen report (first feature), the last chord on the outro.
# Tempo chosen so both are on the start of a bar: 160 beats between them -> 119.7 BPM.
# ---------------------------------------------------------------------------------------------------------------
def generated():
    drop, outro, meta = START["ReportPipeline"], START["Outro"], START["PoweredByMeta"]
    beat = (outro - drop) / 160
    bpm = 60 / beat
    tr = Track(LENGTH)
    # I - vi - IV - V in D major, one chord per bar
    chords = [[50, 54, 57, 62], [47, 50, 54, 59], [43, 50, 55, 59], [45, 49, 52, 57]]
    roots = [38, 35, 31, 33]
    bar = 4 * beat
    first_bar = drop - bar * int(drop / bar + 1)        # the grid extends back before the drop
    bars = [first_bar + k * bar for k in range(int((LENGTH - first_bar) / bar) + 2)]

    kicks = []
    for b_i, b0 in enumerate(bars):
        ch, rt = chords[b_i % 4], roots[b_i % 4]
        in_intro, in_build, in_main = b0 + bar <= START["LogoReveal"] + 0.01, b0 < drop, drop <= b0 < meta
        in_break, in_end = meta <= b0 < outro, b0 >= outro
        # pad: always there except the very end; opens up after the drop
        if b0 < outro and b0 + bar > 0:
            cutoff = 900 + 1700 * min(1, max(0, b0 + bar) / drop) if b0 < drop else 2600
            tr.place(pad(ch, bar + 0.35, cutoff=cutoff, attack=0.25, release=0.35), max(0, b0), 0.55)
        for q in range(16):                               # 16th notes
            t = b0 + q * beat / 4
            if t < 0 or t >= LENGTH:
                continue
            on_beat, offbeat = q % 4 == 0, q % 4 == 2
            if in_main:
                if on_beat:
                    tr.place(kick(), t, 0.9)
                    kicks.append(t)
                if q in (4, 12):
                    tr.place(clap(), t, 0.45, 0.05)
                if offbeat:
                    tr.place(hat(True), t, 0.16, 0.25)
                tr.place(hat(), t, 0.10 if q % 2 else 0.06, -0.25)
                if offbeat:                               # offbeat bass pluck, octave above the root
                    tr.place(pluck(hz(rt + 12), 0.28, 900, 11) + pluck(hz(rt), 0.28, 400, 9) * 0.8, t, 0.55)
                if b0 >= START["TicketSlider"]:           # arpeggio joins from the third feature
                    note = ch[[0, 1, 2, 3, 2, 1, 3, 2][q % 8]] + 12
                    tr.place(pluck(hz(note), 0.2, 3200, 14), t, 0.13, 0.3 if q % 2 else -0.3)
            elif in_build and b0 + bar > START["LogoReveal"]:
                if on_beat:
                    tr.place(kick(0.5), t, 0.55)
                if offbeat:
                    tr.place(pluck(hz(rt + 12), 0.28, 700, 11), t, 0.4)
                tr.place(hat(), t, 0.07, -0.2)
            elif in_intro and q % 2 == 0 and t > 2.4:     # hats creeping in during the hook
                tr.place(hat(), t, 0.04 + 0.05 * (t / START["LogoReveal"]), -0.2)
            elif in_break:
                if b0 >= outro - 2 * bar and on_beat:      # kick comes back for the last two bars
                    tr.place(kick(0.7), t, 0.6)
                if q % 2 == 0:
                    note = ch[[0, 2, 1, 3][q // 2 % 4]] + 12
                    tr.place(pluck(hz(note), 0.25, 2600, 10), t, 0.12, 0.3 if q % 4 else -0.3)
    # build-ups and accents
    tr.place(riser(START["LogoReveal"] - 1.5, 300, 5000), 1.5, 0.12)
    tr.place(snare_roll(4 * beat), drop - 4 * beat, 0.22)
    tr.place(riser(4 * beat, 400, 7000), drop - 4 * beat, 0.16)
    tr.place(crash(), drop, 0.22)
    for c in CUTS:                                       # a light crash on every scene change in the main part
        if drop < c < meta:
            tr.place(crash(1.0), c, 0.08)
    tr.place(riser(outro - meta, 200, 6000), meta, 0.15)
    tr.place(snare_roll(4 * beat, 4, 20), outro - 4 * beat, 0.22)
    # the end: one big chord and kick on the outro, ringing out to the last frame
    tr.place(kick(1.2), outro, 1.0)
    tr.place(crash(3.0), outro, 0.25)
    tr.place(pad([50, 54, 57, 62, 66], LENGTH - outro, cutoff=2600, attack=0.02, release=2.5), outro, 0.75)
    tr.place(sub(hz(38), LENGTH - outro, 0.01, 3.0), outro, 0.5)
    # side-chain: pads and bass dip after each kick (the "pumping" of the genre)
    g = np.ones(tr.n)
    for k in kicks:
        i = int(k * SR)
        n = min(int(0.25 * SR), tr.n - i)
        g[i:i + n] = np.minimum(g[i:i + n], 1 - 0.45 * np.exp(-np.arange(n) / SR / 0.09))
    tr.buf *= g[:, None] * 0.6 + 0.4
    tr.buf = reverb(tr.buf, 1.4, 0.18)
    end_fade(tr, 1.2)
    save(tr, "generated")
    print(f"  {bpm:.1f} BPM, drop at {drop:.1f} s, outro hit at {outro:.1f} s")


# ---------------------------------------------------------------------------------------------------------------
# Version 3: shaped by the reference analysis (audio/reference_analysis.json):
#   tempo 95.7 BPM -> 95.9 BPM here, so the logo reveal and the outro both fall on a beat (134 beats apart)
#   key A minor (A and E strongest, almost a drone on the fifth) -> A minor, with a moving progression of its own
#   dark and smooth: 94% of the energy under 250 Hz, very little percussion (5%), low brightness -> sub bass, dark pad,
#     soft kick, rim, no bright drums, everything low-passed
#   structure: entry from silence at ~3%, long steady plateau, a softer dip at 67-90%, a strong rise to a climax at
#     ~93%, sudden end -> entry on the logo, plateau through the features, dip from "Updates", rise through
#     "Powered by Meta", climax on the outro, clean end on the last frame
# ---------------------------------------------------------------------------------------------------------------
def dark_bass(freq, length=0.4, decay=6.0):
    """Sine bass with a touch of octave: no odd overtones, so no C sharp ringing over the A (keeps it minor)."""
    t = np.arange(int(length * SR)) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return x * np.exp(-t * decay) * np.minimum(t / 0.004, 1)


def inspired_track(length, entry, outro, cuts, dip=None, rise=None, bell_in=None, calm=False, fade_in=0.0,
                   end_fade_s=0.6):
    """The version 3 music on any timeline. entry: where the track comes in; outro: the climax (or the end, when calm);
    dip..rise: a softer stretch; rise..outro: the build; calm: a quiet bed with no drums, for under the live demo."""
    dip = dip if dip is not None else outro
    rise = rise if rise is not None else outro
    bell_in = bell_in if bell_in is not None else entry
    n = max(4, round((outro - entry) / (60 / 95.9)))
    beat = (outro - entry) / n                            # about 95.9 BPM, so entry and outro both fall on a beat
    tr = Track(length)
    # i - VImaj7 - iv9 - vsus4/v, two bars each (Am, Fmaj7, Dm9, Esus4 -> Em): natural minor throughout, no G sharp,
    # so the track stays in A minor like the reference
    prog = [([57, 60, 64], 33), ([53, 57, 60, 64], 29), ([50, 53, 57, 60, 64], 38), ([52, 57, 59], 28)]
    bar = 4 * beat
    if entry > 0.5:                                       # a dark drone swells in, like the reference's entry
        tr.place(sub(hz(33), entry + 0.3, min(3.5, entry), 0.3) * 0.8 + sub(hz(40), entry + 0.3, min(4.0, entry), 0.3) * 0.25, 0, 0.9)
        tr.place(lp(riser(entry, 80, 900), 1200), 0, 0.15)
    # an original motif in A minor pentatonic for the bells (not taken from the reference)
    motif = [(0, 76), (1.5, 79), (2, 81), (3, 79), (4.5, 76), (5, 74), (6, 72), (7, 74)]
    b_i, b0 = 0, entry
    while b0 < outro:
        notes, root = prog[(b_i // 2) % 4]
        if b_i % 2 == 1 and (b_i // 2) % 4 == 3:
            notes = [52, 55, 59, 64]                      # Esus4 resolves to Em in its second bar
        quiet = calm or dip <= b0 < rise
        building = not calm and b0 >= rise
        k = (b0 - rise) / (outro - rise) if building else 0
        level = 0.55 if quiet else 1.0
        tr.place(pad(notes, bar + 0.6, cutoff=650 if quiet else 900 + 1200 * k, attack=0.6, release=0.6), b0, 0.6 * level)
        tr.place(sub(hz(root), bar + 0.05, 0.08, 0.15), b0, 0.95 * level)
        for q in range(8):                                # 8th notes
            t = b0 + q * beat / 2
            if t >= outro:
                break
            if not quiet:
                if q % 4 == 0 or (building and q % 2 == 0 and k > 0.4):
                    tr.place(soft_kick(), t, 0.7 + 0.3 * k)
                tr.place(dark_bass(hz(root + 12), 0.4, 6), t, 0.42 + 0.2 * k)      # dark pulsing bass
                if q == 6 and b_i % 2 == 1:
                    tr.place(rim(), t, 0.12, 0.2)
            elif q % 4 == 0:
                tr.place(dark_bass(hz(root + 12), 0.6, 4), t, 0.32)
        if bell_in <= b0 < dip and b_i % 4 in (0, 1) and (not calm or b_i % 8 == 0):
            for off, m in motif:
                if off < 4 * (2 if b_i % 4 == 0 else 1) and (b_i % 4 == 0 or off >= 4):
                    t = b0 + (off - (4 if b_i % 4 == 1 else 0)) * beat
                    tr.place(bell(hz(m), 1.4), t, 0.07, 0.35)
        b_i += 1
        b0 += bar
    if not calm:
        for c in cuts:                                    # strong beats on every scene change: a low thump on the cut
            if entry <= c < outro:
                tr.place(soft_kick(), c, 0.55)
        if rise < outro:
            tr.place(riser(outro - rise, 120, 2600), rise, 0.12)
        tr.place(soft_kick(), entry, 1.0)                 # the entry
        if outro < length:                                # climax, then it rings out to the last frame
            tr.place(kick(0.6), outro, 0.9)
            tr.place(sub(hz(33), length - outro, 0.01, 2.5), outro, 1.0)
            tr.place(pad([45, 52, 57, 60, 64], length - outro, cutoff=1600, attack=0.03, release=2.2), outro, 0.8)
    tr.buf = reverb(tr.buf, 2.4, 0.22, 2200)
    if fade_in:
        n_in = int(fade_in * SR)
        tr.buf[:n_in] *= np.linspace(0, 1, n_in)[:, None] ** 1.5
    end_fade(tr, end_fade_s)
    return tr, 60 / beat


def inspired():
    """Version 3, on the full trailer."""
    tr, bpm = inspired_track(LENGTH, START["LogoReveal"], START["Outro"], CUTS, dip=START["Updates"],
                             rise=START["PoweredByMeta"], bell_in=START["ReportPipeline"])
    save(tr, "inspired")
    print(f"  {bpm:.1f} BPM")


def final_video():
    """The final film: the short trailer (src/timeline_short.json) then the logo transition, with one track that climaxes
    on the cut to the transition and fades out during it; then a calm, quieter bed under the live demo, which fades out
    at the 3:00 mark; then a short closing phrase under the outro."""
    tl = json.loads((ROOT / "src" / "timeline_short.json").read_text())
    fps = tl["fps"]
    st, at = {}, 0
    for s in tl["scenes"]:
        st[s["name"]] = at / fps
        at += s["frames"] - (0 if s["into_next"] == "cut" else tl["transition"])
    trailer_end, sting = at / fps, tl["sting_frames"] / fps
    cuts = [st[s["name"]] for s in tl["scenes"][1:]]
    tr, bpm = inspired_track(trailer_end + sting, st["LogoReveal"], trailer_end, cuts, rise=st["ModelBadges"],
                             bell_in=st["ReportPipeline"], end_fade_s=sting * 0.9)
    save(tr, "final_trailer")
    print(f"  trailer + transition: {trailer_end + sting:.2f} s, {bpm:.1f} BPM, climax on the cut at {trailer_end:.2f} s")
    demo = (tl["film_frames"] - at - tl["sting_frames"]) / fps
    bed, bpm = inspired_track(demo, 0.0, demo, [], calm=True, fade_in=3.0, end_fade_s=3.0)
    save(bed, "final_demo_bed")
    print(f"  demo bed: {demo:.2f} s, calm, fades in over 3 s")
    outro = tl["outro_frames"] / fps
    end, bpm = inspired_track(outro, 0.0, outro - 2.8, [], rise=0.0, end_fade_s=1.4)
    save(end, "final_outro")
    print(f"  outro: {outro:.2f} s, builds to a last hit at {outro - 2.8:.2f} s")


# ---------------------------------------------------------------------------------------------------------------
# Version 4: laid-back cinematic hip-hop, in the mood of a crime-city open-world soundtrack (an original composition):
# deep gliding 808, crisp snare on 2 and 4, swung hi-hats, electric piano chords, a dark pad and a mellow whistle lead.
# D minor, ~93 BPM: a steady head-nod groove that wakes people up without rushing them.
# ---------------------------------------------------------------------------------------------------------------
NOISE = np.random.default_rng(23)


def epiano(freq, length=1.6):
    """Electric piano: a sine carrier with a decaying FM "tine" and a slow tremolo."""
    t = np.arange(int(length * SR)) / SR
    index = 1.6 * np.exp(-t * 6) + 0.25
    x = np.sin(2 * np.pi * freq * t + index * np.sin(2 * np.pi * freq * t))
    return x * np.exp(-t * 1.3) * (1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)) * np.minimum(t / 0.004, 1)


def bass808(freq, length, glide_from=None):
    """808 bass: saturated sine with a short glide from the previous note."""
    t = np.arange(int(length * SR)) / SR
    f = np.full(len(t), freq) if glide_from is None else freq + (glide_from - freq) * np.exp(-t * 18)
    x = np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 1.8) * np.exp(-t * 1.1) * np.minimum(t / 0.005, 1)
    n = min(len(t), int(0.03 * SR))
    x[-n:] *= np.linspace(1, 0, n)
    return lp(x, 900)


def snare():
    t = np.arange(int(0.32 * SR)) / SR
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 28)
    noise = lp(hp(NOISE.standard_normal(len(t)), 1200), 9000) * np.exp(-t * 16)
    return np.tanh((body * 0.7 + noise) * 1.2)


def whistle(freq, length, from_freq=None):
    """Mellow lead: a sine with a little breath, vibrato after the attack, and a glide from the previous note."""
    t = np.arange(int(length * SR)) / SR
    f = np.full(len(t), freq) if from_freq is None else freq + (from_freq - freq) * np.exp(-t * 25)
    f = f * (1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(t / 0.35, 1))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.08 * lp(hp(NOISE.standard_normal(len(t)), 2000), 5000)
    env = np.minimum(t / 0.05, 1) * np.clip((length - t) / 0.12, 0, 1)
    return lp(x, 3500) * env


def streets():
    drop, logo, outro, meta = START["ReportPipeline"], START["LogoReveal"], START["Outro"], START["PoweredByMeta"]
    beat = (outro - drop) / 124                           # 31 bars between the drop and the outro: ~92.8 BPM
    bpm, bar, step = 60 / beat, 4 * beat, beat / 4
    swing = 0.18 * step                                   # off 16ths pushed late: the lazy hip-hop feel
    tr = Track(LENGTH)
    # Dm9 - Bbmaj7 - Gm9 - A7sus4 > A7, one chord per bar
    chords = [[50, 53, 57, 60, 64], [46, 50, 53, 57], [43, 46, 50, 53, 57], [45, 50, 52, 55]]
    roots = [38, 34, 31, 33]
    lead = [(0, 74, 1.5), (1.5, 72, 0.5), (2, 69, 1.0), (3, 72, 1.0), (4, 77, 1.5), (5.5, 76, 0.5), (6, 74, 2.0)]
    b0 = drop - bar * int(drop / bar + 1)                 # the bar grid extends back before the drop
    b_i, prev_root = 0, None
    while b0 < outro:
        ch, rt = chords[b_i % 4], roots[b_i % 4]
        ch2 = [45, 49, 52, 55] if b_i % 4 == 3 else ch   # A7: the sus4 resolves halfway through the bar
        intro, build = b0 < logo - 0.01, logo - 0.01 <= b0 < drop
        main, breakdown = drop <= b0 < meta, meta <= b0 < outro
        # keys: a laid-back stab on the one (slightly strummed) and a softer one on the "and" of two
        if b0 + bar > 0:
            for j, m in enumerate(ch):
                tr.place(epiano(hz(m), 2.2), max(0, b0) + j * 0.012, 0.16 * (0.6 if intro else 1), -0.15 + 0.08 * j)
            for j, m in enumerate(ch2):
                tr.place(epiano(hz(m + 12 if m < 50 else m), 0.9), max(0, b0 + 6 * step + swing) + j * 0.01, 0.09, 0.15)
            tr.place(pad(ch, bar + 0.4, cutoff=650 if intro else 1000, attack=0.5, release=0.5), max(0, b0), 0.25)
        for q in range(16):
            t = b0 + q * step + (swing if q % 2 else 0)
            if t < 0 or t >= outro:
                continue
            if main:
                if q in (0, 10):
                    tr.place(kick(0.6), t, 0.75)
                if q in (4, 12):
                    tr.place(snare(), t, 0.5, 0.05)
                if q % 2 == 0 or (b_i % 4 == 3 and q >= 13):
                    tr.place(hat(), t, 0.10 if q % 4 == 0 else 0.07, -0.25)
                if q == 14 and b_i % 2:
                    tr.place(hat(True), t, 0.07, 0.3)
            elif build and q % 2 == 0:
                tr.place(hat(), t, 0.06, -0.25)
            elif breakdown:                               # lighter groove under "Powered by Meta": one 808 per bar
                if q == 0:
                    tr.place(kick(0.4), t, 0.5)
                    tr.place(bass808(hz(rt), 2.2 * beat, hz(prev_root) if prev_root else None), t, 0.5)
                if q in (4, 12):
                    tr.place(snare(), t, 0.26, 0.05)
                if q % 4 == 0:
                    tr.place(hat(), t, 0.06, -0.25)
        # 808: on the one (gliding from the last root), a push on the "a" of two, and one on the "and" of three
        if main:
            for q, length, glide in ((0, 1.7 * beat, prev_root), (7, 0.9 * beat, None), (10, 1.4 * beat, None)):
                t = b0 + q * step + (swing if q % 2 else 0)
                if 0 <= t < outro:
                    tr.place(bass808(hz(rt), length, hz(glide) if glide else None), t, 0.7)
        # the whistle lead answers every other 4-bar phrase, from the map scene on
        if main and b0 >= START["MapScene"] and (b_i // 4) % 2 == 1 and b_i % 4 in (0, 2):
            prev = None
            for off, m, ln in lead:
                tr.place(whistle(hz(m), ln * beat * 0.95, hz(prev) if prev else None), b0 + off * beat, 0.11, 0.2)
                prev = m
        prev_root, b0, b_i = rt, b0 + bar, b_i + 1
    # transitions: a soft riser into the logo, the 808 stepping in with it, a snare fill into the drop,
    # a filtered build through "Powered by Meta" into the outro
    tr.place(lp(riser(logo, 150, 2500), 3000), 0, 0.10)
    tr.place(bass808(hz(38), 2.0), logo, 0.6)
    for k in range(8):
        tr.place(snare(), drop - 2 * beat + k * beat / 4, 0.12 + 0.03 * k)
    tr.place(lp(riser(outro - meta, 150, 3000), 3500), meta, 0.12)
    # the end: a last 808 and chord on the outro, ringing out to the final frame
    tr.place(kick(0.6), outro, 0.9)
    tr.place(snare(), outro, 0.35)
    tr.place(bass808(hz(38), LENGTH - outro), outro, 0.95)
    for j, m in enumerate([50, 53, 57, 60, 64, 69]):
        tr.place(epiano(hz(m), LENGTH - outro), outro + j * 0.015, 0.26)
    tr.place(pad([50, 57, 60, 65], LENGTH - outro, cutoff=1100, attack=0.05, release=2.5), outro, 0.45)
    tr.buf = reverb(tr.buf, 1.6, 0.2, 2600)
    end_fade(tr, 0.8)
    save(tr, "streets", -19.0)
    print(f"  {bpm:.1f} BPM, 808 in at {logo:.1f} s, drop at {drop:.1f} s, breakdown from {meta:.1f} s, final hit at {outro:.1f} s")


if __name__ == "__main__":
    import sys
    print(f"trailer: {LENGTH:.2f} s; scene changes at " + ", ".join(f"{c:.1f}" for c in CUTS))
    for name in sys.argv[1:] or ["generated", "inspired", "streets"]:  # also: final_video
        globals()[name]()
