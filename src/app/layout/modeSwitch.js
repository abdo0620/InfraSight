export function initModeSwitch(onToggle) {
  document.getElementById('mode-toggle').addEventListener('click', onToggle);
}

export function updateModeSwitch(mode) {
  document.documentElement.dataset.mode = mode;
  document.getElementById('label-citizen').classList.toggle('is-active', mode === 'citizen');
  document.getElementById('label-municipal').classList.toggle('is-active', mode === 'municipal');
}
