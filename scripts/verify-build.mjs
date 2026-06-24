import {existsSync, readFileSync} from 'fs';
import {join} from 'path';

const dist = join(process.cwd(), '.next');
const appRoutesPath = join(dist, 'app-path-routes-manifest.json');
const prerenderPath = join(dist, 'prerender-manifest.json');

const report = {appRoutesPath, hasAppRoutesFile: existsSync(appRoutesPath), routes: [], prerenderRoutes: []};

if (report.hasAppRoutesFile) {
  const manifest = JSON.parse(readFileSync(appRoutesPath, 'utf8'));
  report.routes = Object.keys(manifest);
}

if (existsSync(prerenderPath)) {
  const prerender = JSON.parse(readFileSync(prerenderPath, 'utf8'));
  report.prerenderRoutes = Object.keys(prerender.routes ?? {});
}

console.log('[verify-build] app routes:', report.routes.join(', ') || 'NONE');
console.log('[verify-build] prerender routes:', report.prerenderRoutes.join(', ') || 'NONE');

const hasPagesIndex =
  existsSync(join(dist, 'server/pages/index.js')) ||
  existsSync(join(dist, 'server/pages/index.html'));

console.log('[verify-build] pages index:', hasPagesIndex);

const hasPagesApi =
  existsSync(join(dist, 'server/pages/api/chat.js')) ||
  existsSync(join(dist, 'server/pages/api/chat.html'));

console.log('[verify-build] pages api/chat:', hasPagesApi);

const hasRoot =
  report.routes.includes('/page') ||
  report.prerenderRoutes.includes('/') ||
  hasPagesIndex ||
  hasPagesApi;

if (!hasRoot) {
  console.error('[verify-build] FAIL: no root route in build output');
  process.exit(1);
}

console.log('[verify-build] OK: root route present');
