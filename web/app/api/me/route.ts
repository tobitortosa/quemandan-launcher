import { ok, requireUser } from '@/lib/api';

/** La pantalla de espera del launcher consulta esto para saber si ya lo aprobaron. */
export async function GET(request: Request) {
  const guard = await requireUser(request);
  if ('response' in guard) return guard.response;

  const { user } = guard;
  return ok({
    username: user.username,
    status: user.status,
    role: user.role,
    createdAt: user.createdAt,
  });
}
