// Usage: npm run new:page <citizen|municipal> <name> ["Menu title"]
// Creates src/features/<mode>/<name>/index.js and registers it in src/app/modes.js.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [mode, name, ...rest] = process.argv.slice(2);
const fail = (m) => { console.error('Error: ' + m + '\nUsage: npm run new:page <citizen|municipal> <name> ["Menu title"]'); process.exit(1); };

if (!['citizen', 'municipal'].includes(mode)) fail('mode must be citizen or municipal');
if (!name || !/^[a-z][a-z0-9]*$/.test(name)) fail('name must be lowercase letters/digits, e.g. "payments"');

const Cap = (s) => s[0].toUpperCase() + s.slice(1);
const title = rest.join(' ') || Cap(name);
const dir = path.join(root, 'src/features', mode, name);
if (fs.existsSync(dir)) fail(`${dir} already exists`);

fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, 'index.js'), `import { pageHeader } from '../../../shared/ui/pageHeader.js';

export default {
  id: '${name}',
  title: '${title.replace(/'/g, "\\'")}',
  render: () => pageHeader('${title.replace(/'/g, "\\'")}', '${Cap(mode)} mode'),
  // mount(root) { ... }  // optional: attach event handlers after render
};
`);

const modesFile = path.join(root, 'src/app/modes.js');
let src = fs.readFileSync(modesFile, 'utf8');
const v = mode + Cap(name);
src = src.replace('// @imports', `import ${v} from '../features/${mode}/${name}/index.js';\n// @imports`);
src = src.replace(`      // @pages:${mode}`, `      ${v},\n      // @pages:${mode}`);
fs.writeFileSync(modesFile, src);

console.log(`Created src/features/${mode}/${name}/index.js and added it to the ${mode} menu.`);
