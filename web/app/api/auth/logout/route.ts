import { ok } from '@/lib/api';
import { bearerToken, revokeSession } from '@/lib/auth';

export async function POST(request: Request) {
  const token = bearerToken(request);
  if (token) await revokeSession(token);
  return ok({ ok: true });
}
