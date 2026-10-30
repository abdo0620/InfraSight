# Portal

Minimal two-mode web portal (Citizen / Municipal) with a side menu and a light/dark mode switch.

## Run
ES modules need a local server (they do not load from `file://`):

    python3 -m http.server 8000   # then open http://localhost:8000

## Structure
    index.html               App shell
    src/css/                 tokens (colors) · base · layout · components
    src/js/main.js           Entry point
    src/js/config/routes.js  Modes and their pages
    src/js/core/router.js    Hash router (#mode-page)
    src/js/components/       sidebar, modeSwitch, pageShell
    src/js/pages/<mode>/     One file per page

## Add a page
1. Create `src/js/pages/<mode>/<name>.js` (copy an existing one).
2. Import it and add it to that mode in `src/js/config/routes.js`.
