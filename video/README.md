# InfraSight demo video

The demo video for the hackathon, made from code:

- **The final film** (`FinalVideo`, 3:00 + an 8 s outro): a 30 s trailer (`TrailerShort`), a 3 s logo transition
  (`LogoSting`), then a live demo of the real app recorded in one take (`live/`).
- **The full trailer** (`Trailer`, about 95 s), made with [Remotion](https://www.remotion.dev/) (React), 1920x1080, 30 fps.
- **Music and sound effects**, all original, synthesized in Python (`audio/`).

```bash
cd video
npm install
npm run studio     # preview and scrub in the browser
npm run render     # writes out/infrasight-trailer.mp4
```

## How it looks like the app
`src/Root.tsx` loads the app's own stylesheet (`frontend/css/styles.css`) and its fonts (Inter, Newsreader), and the
scenes rebuild the app's markup with the same classes (`.panel`, `.btn`, `.pipe-card`, `.cmp`, `.tabs`, ...). The app's
screens are plain JavaScript templates, not React components, so they are rebuilt here rather than imported.
`Window` in `src/lib.tsx` shows the UI zoomed (about 1.4x) so it stays readable on a phone.

Images in `public/img/` come from the app: a real bus shelter report run through Muse Spark, SAM 3.1 and Muse Image,
the demo pothole and manhole tickets, the staff map, a detour, and the pages of a generated PDF report.

## Scenes (`src/scenes/`, in order, set in `src/Trailer.tsx`)
| Scene | Length | What happens |
|---|---|---|
| `Hook` | 6 s | The problem, in kinetic type |
| `LogoReveal` | 4 s | The radar logo draws itself, name and tagline |
| `ReportPipeline` | 12 s | A citizen reports the bus shelter, then the live AI panel: Muse Spark, SAM 3.1, Muse Image |
| `MapScene` | 6 s | The staff map: incidents, danger zones, detours, hotspots |
| `TicketSlider` | 8 s | The before / after slider, the SAM outline and the repair preview |
| `FullReport` | 10 s | Live progress of the full report, then the sourced cost table |
| `Detour` | 8 s | The detour draws itself; the traffic order types itself |
| `Duplicates` | 5 s | Two reports of the same pothole merge into one ticket |
| `Stages` | 6 s | The 7 legal stages and an AI draft |
| `RepairCheck` | 5 s | Before / after comparison and the verdict |
| `Updates` | 5 s | Citizen updates in several languages |
| `Dashboard` | 6 s | Figures, priority matrix, weekly brief, hotspot |
| `PdfReport` | 4 s | The PDF report's pages fan out |
| `PoweredByMeta` | 10 s | How Muse Spark, SAM 3.1 and Muse Image work together |
| `Outro` | 6 s | Name, repository, hackathon |

`scripts/stills.mjs` renders single frames to check a scene without rendering the video:
`node scripts/stills.mjs <out dir> 300 900 1500`.

## Sound (`audio/`)
`make_sfx.py` synthesizes the effects (`public/sfx/`), `make_music.py` the music tracks (`public/music/`, not committed:
about 18 MB each), from the building blocks in `synth.py`. No samples, loops or third-party recordings are used.
`analyze_reference.py` measured the tempo, key and energy curve of a reference video (kept out of the repository) to
inspire the "inspired" track; nothing of it is in the video. `npm run sound` rebuilds everything.

## The live demo (`live/`)
`record_demo.py` drives the running app in headless Edge through the DevTools protocol (real clicks, real typing, real
Meta Model API calls) and saves every screen update. Headless rendering of the app at 1920x1080 gives only a few frames
a second, so the take is recorded in slow motion (CSS animations, scrolls, drags and pauses 10x slower) and played back
at real speed. Live AI calls run at their real speed and are shown sped up, labelled with their real duration; the
mouse pointer moves along human-like paths and is drawn by `assemble_demo.py` at 30 fps, with the captions.

```bash
# the app running on http://localhost:8005 with fresh demo data (SEED_DEMO=true), then:
python live/record_demo.py http://localhost:8005 <take dir> <photo> <second photo>     # about 40 min
python live/assemble_demo.py <take dir> public/live/live_demo.mp4 <ffmpeg> 147.4        # fitted to 147.4 s
```

## The final film
```bash
python audio/make_music.py final_video          # music fitted to src/timeline_short.json
npx remotion render src/index.ts FinalVideo out/final_video.mp4 --codec=h264 --crf=16 --scale=1.3333333333333333
```
`src/timeline_short.json` sets the trailer scenes (`skip`: frames cut from the start of a scene, so the AI waits are
not shown), the length of the film (`film_frames`, 3:00) and of the outro. The live demo fills what is left of the 3:00.
