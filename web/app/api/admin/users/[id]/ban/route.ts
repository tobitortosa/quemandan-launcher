import { eq } from 'drizzle-orm';
import { fail, ok, pterodactylFailure, readJson, requireAdmin } from '@/lib/api';
import { revokeSessions } from '@/lib/auth';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { kick, whitelist } from '@/lib/pterodactyl';

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const id = Number.parseInt((await context.params).id, 10);
  if (!Number.isFinite(id)) return fail('Id de usuario inválido.');

  const rows = await db.select().from(users).where(eq(users.id, id)).limit(1);
  const user = rows[0];
  if (!user) return fail('Esa cuenta no existe.', 404);
  if (user.role === 'admin') return fail('No se puede banear una cuenta de administrador.');

  const body = await readJson<{ reason?: string }>(request);
  const reason = body?.reason?.trim() || 'Baneado';

  try {
    // Sacarlo de la whitelist no echa a quien ya está jugando: por eso también el kick.
    await whitelist.remove(user.username);
    await kick(user.username, reason);
  } catch (error) {
    return pterodactylFailure(error, `Banear a ${user.username}`);
  }

  await db.update(users).set({ status: 'banned', bannedAt: new Date() }).where(eq(users.id, id));
  await revokeSessions(id);

  return ok({ username: user.username, status: 'banned' });
}
