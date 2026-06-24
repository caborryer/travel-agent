import {NextRequest, NextResponse} from 'next/server';
import {z} from 'zod';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const ChatRequestSchema = z.object({
  message: z
    .string()
    .min(1, 'Message must not be empty')
    .max(2000, 'Message must not exceed 2000 characters'),
  session_id: z.string().min(1).max(100).optional(),
});

export async function POST(req: NextRequest) {
  try {
    const raw = await req.json();
    const parsed = ChatRequestSchema.safeParse(raw);

    if (!parsed.success) {
      const firstIssue = parsed.error.issues[0];
      return NextResponse.json(
        {error: `Validation error: ${firstIssue.path.join('.')} - ${firstIssue.message}`},
        {status: 400},
      );
    }

    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(parsed.data),
    });

    if (!res.ok) {
      const error = await res.text();
      return NextResponse.json({error}, {status: res.status});
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      {error: 'Failed to connect to backend'},
      {status: 503},
    );
  }
}
