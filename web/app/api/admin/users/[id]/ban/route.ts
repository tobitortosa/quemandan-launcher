import { eq } from 'drizzle-orm';
import { fail, ok, pterodactylFailure, readJson, requireAdmin } from '@/lib/api';
import { revokeSessions } from '@/lib/auth';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { kick } from '@/lib/pterodactyl';
import { syncWhitelist } from '@/lib/whitelist';

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

  await db.update(users).set({ status: 'banned', bannedAt: new Date() }).where(eq(users.id, id));

  try {
    // Al reescribir la whitelist ya no figura. Sacarlo de la lista no echa a quien está
    // jugando en ese momento, así que además se lo expulsa.
    await syncWhitelist();
    await kick(user.username, reason);
  } catch (error) {
    await db.update(users).set({ status: user.status, bannedAt: user.bannedAt }).where(eq(users.id, id));
    return pterodactylFailure(error, `Banear a ${user.username}`);
  }

  await revokeSessions(id);

  return ok({ username: user.username, status: 'banned' });
}
