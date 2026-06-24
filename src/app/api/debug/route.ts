import {NextResponse} from 'next/server';
import {readFileSync, existsSync} from 'fs';
import {join} from 'path';

export async function GET() {
  const manifestPath = join(process.cwd(), '.next/server/app-paths-manifest.json');
  let manifest: Record<string, string> | null = null;
  let manifestError: string | null = null;

  try {
    if (existsSync(manifestPath)) {
      manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
    } else {
      manifestError = 'manifest not found at build/runtime';
    }
  } catch (e) {
    manifestError = e instanceof Error ? e.message : 'read failed';
  }

  const payload = {
    ok: true,
    hypothesisId: 'H1-H4',
    vercel: process.env.VERCEL === '1',
    vercelEnv: process.env.VERCEL_ENV ?? null,
    nodeEnv: process.env.NODE_ENV ?? null,
    cwd: process.cwd(),
    hasPageRoute: manifest ? '/page' in manifest : false,
    hasApiChat: manifest ? '/api/chat/route' in manifest : false,
    manifestKeys: manifest ? Object.keys(manifest) : [],
    manifestError,
    backendUrl: process.env.BACKEND_URL ? 'set' : 'missing',
  };

  // #region agent log
  fetch('http://127.0.0.1:7659/ingest/0d5509eb-d124-40cc-804a-9d903d6a96c6', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-Debug-Session-Id': 'df77db'},
    body: JSON.stringify({
      sessionId: 'df77db',
      runId: 'vercel-debug',
      hypothesisId: 'H1-H4',
      location: 'api/debug/route.ts:GET',
      message: 'debug route hit',
      data: payload,
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion

  return NextResponse.json(payload);
}
