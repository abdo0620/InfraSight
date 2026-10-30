// Page registry: the only file that knows which pages exist.
// `npm run new:page <mode> <name>` adds lines at the @markers. Order here = order in the side menu.
import citizenHome from '../features/citizen/home/index.js';
import citizenRequests from '../features/citizen/requests/index.js';
import citizenServices from '../features/citizen/services/index.js';
import citizenProfile from '../features/citizen/profile/index.js';
import municipalDashboard from '../features/municipal/dashboard/index.js';
import municipalCases from '../features/municipal/cases/index.js';
import municipalReports from '../features/municipal/reports/index.js';
import municipalSettings from '../features/municipal/settings/index.js';
// @imports

export const MODES = {
  citizen: {
    label: 'Citizen',
    pages: [
      citizenHome,
      citizenRequests,
      citizenServices,
      citizenProfile,
      // @pages:citizen
    ],
  },
  municipal: {
    label: 'Municipal',
    pages: [
      municipalDashboard,
      municipalCases,
      municipalReports,
      municipalSettings,
      // @pages:municipal
    ],
  },
};
