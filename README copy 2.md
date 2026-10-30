# Portal (InfraSight)

Two-mode web app: **Citizen** reports damaged infrastructure; **Municipal** triages cases and generates PDF reports.
Light/dark switch in the top-right corner changes mode. See [docs/PITCH.md](docs/PITCH.md) for the idea.

## Run
```
npm start                      # or: python3 -m http.server 8000
npm test                       # unit tests
npm run new:page citizen faq   # scaffold a new page
```
ES modules need a server; opening `index.html` directly will not work.

## Status
`AI.useMock = true` in `src/config.js`: the AI pipeline is simulated in the browser. To go live follow [docs/API.md](docs/API.md).

## Where things are
| I want to... | Go to |
|---|---|
| add a page | `npm run new:page` · [docs/ADDING_FEATURES.md](docs/ADDING_FEATURES.md) |
| change colors | `src/styles/tokens.css` |
| change the AI steps | `src/services/ai/` |
| change how data is stored | `src/services/storage/` |
| change the PDF | `src/services/pdf/reportPdf.js` |
| see the big picture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |

## Pages
| Citizen | Municipal |
|---|---|
| Home (empty) | Dashboard (empty) |
| **Requests**: photo → AI assessment → submit | **Cases**: all requests, most severe first, Generate report |
| Services (empty) | **Reports**: view / download PDFs |
| Profile (empty) | Settings (empty) |
