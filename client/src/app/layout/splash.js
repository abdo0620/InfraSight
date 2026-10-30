const el = () => document.getElementById('splash');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

export const hideSplash = () => el().classList.remove('is-visible');

// Cover the screen, run the change while hidden, then reveal.
export async function withSplash(toMode, change) {
  el().dataset.mode = toMode;            // splash takes the color of the destination mode
  el().classList.add('is-visible');
  await wait(450);                       // wait for the fade-in
  change();
  await wait(500);                       // keep the logo a moment
  hideSplash();
}