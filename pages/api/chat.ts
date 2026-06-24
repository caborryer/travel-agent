import type {NextApiRequest, NextApiResponse} from 'next';
import {z} from 'zod';

const PRODUCTION_BACKEND_URL = 'https://travel-agent-7007.onrender.com';

const BACKEND_URL =
  process.env.BACKEND_URL ||
  (process.env.VERCEL === '1' ? PRODUCTION_BACKEND_URL : 'http://localhost:8000');

const ChatRequestSchema = z.object({
  message: z
    .string()
    .min(1, 'Message must not be empty')
    .max(2000, 'Message must not exceed 2000 characters'),
  session_id: z.string().min(1).max(100).optional(),
});

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({error: 'Method not allowed'});
  }

  try {
    const parsed = ChatRequestSchema.safeParse(req.body);
    if (!parsed.success) {
      const firstIssue = parsed.error.issues[0];
      return res.status(400).json({
        error: `Validation error: ${firstIssue.path.join('.')} - ${firstIssue.message}`,
      });
    }

    // #region agent log
    fetch('http://127.0.0.1:7659/ingest/0d5509eb-d124-40cc-804a-9d903d6a96c6', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-Debug-Session-Id': 'df77db'},
      body: JSON.stringify({
        sessionId: 'df77db',
        runId: 'chat-api',
        hypothesisId: 'H-API',
        location: 'pages/api/chat.ts:handler',
        message: 'proxying chat to backend',
        data: {
          backendUrl: BACKEND_URL,
          vercel: process.env.VERCEL === '1',
          messageLength: parsed.data.message.length,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion

    const backendRes = await fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(parsed.data),
    });

    if (!backendRes.ok) {
      const error = await backendRes.text();
      return res.status(backendRes.status).json({error});
    }

    const data = await backendRes.json();
    return res.status(200).json(data);
  } catch {
    return res.status(503).json({error: 'Failed to connect to backend'});
  }
}
