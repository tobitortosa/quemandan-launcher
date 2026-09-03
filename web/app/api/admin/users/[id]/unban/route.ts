import { eq } from 'drizzle-orm';
import { fail, ok, pterodactylFailure, requireAdmin } from '@/lib/api';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { whitelist } from '@/lib/pterodactyl';

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const id = Number.parseInt((await context.params).id, 10);
  if (!Number.isFinite(id)) return fail('Id de usuario inválido.');

  const rows = await db.select().from(users).where(eq(users.id, id)).limit(1);
  const user = rows[0];
  if (!user) return fail('Esa cuenta no existe.', 404);

  try {
    await whitelist.add(user.username);
  } catch (error) {
    return pterodactylFailure(error, `Desbanear a ${user.username}`);
  }

  await db
    .update(users)
    .set({ status: 'active', bannedAt: null, approvedAt: user.approvedAt ?? new Date() })
    .where(eq(users.id, id));

  return ok({ username: user.username, status: 'active' });
}
