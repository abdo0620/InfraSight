// Single place for settings. No secrets here: keys belong on the backend.
export const DEFAULT_MODE = 'citizen';

export const AI = {
  useMock: true, // true = simulate the AI pipeline in the browser; false = call the backend
  endpoints: {
    segment: '/api/segment',
    assess: '/api/assess',
    repair: '/api/repair',
  },
};
