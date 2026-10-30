# Adding features

## 1. A new page (2 minutes)
```
npm run new:page citizen payments "Payments"
npm run new:page municipal inspections "Inspections"
```
This creates `src/features/<mode>/<name>/index.js` and adds it to the menu in `src/app/modes.js`.
Without Node, copy any placeholder (e.g. `features/citizen/home`) and add two lines to `modes.js`.

Then grow it the same way `requests` is built:
- `index.js` - state and events (`render`, `mount`)
- `view.js` - HTML templates (pure functions: data in, string out)
- `<name>.css` - page styles, then add one `@import` line in `src/styles/main.css`

## 2. New data (a new thing to store)
Add functions to `services/storage/caseStore.js`, or create `services/storage/<thing>Store.js` with the same shape
(`list`, `get`, `add`). Keep the function names stable: that is what lets you swap localStorage for a real backend later.

## 3. A new AI step or API call
1. Add the endpoint to `AI.endpoints` in `src/config.js`.
2. Add the function to `services/ai/mock.js` (fake result) and `services/ai/remote.js` (real call).
3. Export it from `services/ai/index.js`.
4. Document the request/response in `docs/API.md`.
Pages call it from `services/ai/index.js` and never know whether it is mock or real.

## 4. A reusable UI piece
Markup helper: `src/shared/ui/<name>.js`. Style: add the class to `src/styles/components.css`.

## 5. Restyle
Edit `src/styles/tokens.css`. Citizen and Municipal each have their own token block.

## 6. A third mode
The top-right switch is a two-state toggle. For a third mode you need to: add it to `MODES` in `modes.js`,
add a `:root[data-mode="..."]` block in `tokens.css`, add its folder under `src/features/`, and replace the
toggle in `app/layout/modeSwitch.js` with a selector.

## 7. Tests
Add `tests/<name>.test.mjs` and run `npm test`. Services and registries are testable without a browser.

## Checklist before you finish a feature
- [ ] Registered in `app/modes.js`
- [ ] No imports from another feature
- [ ] Colors from tokens only
- [ ] `npm test` passes
- [ ] README/docs updated if you added config or an endpoint
