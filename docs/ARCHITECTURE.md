# Architecture

```
index.html            Shell: top bar, side menu, content area
src/
  main.js             Starts the app
  config.js           Settings (mock on/off, API endpoints)
  app/                The frame around the pages
    app.js            Render loop: route -> sidebar -> page
    modes.js          PAGE REGISTRY (which pages exist, in which mode)
    router.js         Hash router  (#citizen-requests)
    layout/           Sidebar and the mode switch
  features/           One folder per page, grouped by mode
    citizen/<page>/   index.js (behavior) + view.js (HTML) + <page>.css
    municipal/<page>/
  services/           Everything that is not UI
    ai/               SAM / Muse pipeline. index.js picks mock.js or remote.js
    storage/          Cases and reports (shared by both modes)
    pdf/              PDF report builder
  shared/             Small helpers and UI snippets used by many features
  styles/             tokens (colors) · base · layout · components · main.css
docs/                 Guides
scripts/              Tooling (new-page generator)
tests/                node --test
```

## Rules that keep it easy to grow
1. **Features never import other features.** They only use `services/` and `shared/`.
2. **Services never import features.** Data and logic stay UI-free.
3. **One registry.** A page exists only if it is in `app/modes.js`.
4. **Pages return HTML strings.** `render()` returns markup, `mount(root)` attaches events.
5. **Colors and spacing come from `styles/tokens.css`.** No hard-coded colors in features.

## Data flow (current features)
```
Citizen / Requests ──addCase──▶ storage/caseStore ──listCases──▶ Municipal / Cases
                                      │
Municipal / Cases ──addReport─────────┘──listReports──▶ Municipal / Reports ──▶ pdf/reportPdf
```

## Page contract
```js
export default {
  id: 'requests',            // lowercase letters/digits; used in the URL
  title: 'Requests',         // text in the side menu
  render: () => '<html>',    // required: returns markup
  mount: (root) => {},       // optional: attach events after render
};
```
`root` is the content area. Prefer `root.onclick = ...` for page-level click handling (it is reset on every navigation).
