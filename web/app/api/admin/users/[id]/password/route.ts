import { randomBytes } from 'node:crypto';
import { eq } from 'drizzle-orm';
import { fail, ok, requireAdmin } from '@/lib/api';
import { hashPassword, revokeSessions } from '@/lib/auth';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

/**
 * Contraseña temporal. No hay email, así que cuando alguien la olvida el admin le
 * genera una y se la pasa. El nombre no se puede cambiar: cambiarlo sería perder
 * el inventario.
 */
export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const id = Number.parseInt((await context.params).id, 10);
  if (!Number.isFinite(id)) return fail('Id de usuario inválido.');

  const rows = await db.select({ username: users.username }).from(users).where(eq(users.id, id)).limit(1);
  const user = rows[0];
  if (!user) return fail('Esa cuenta no existe.', 404);

  const password = randomBytes(6).toString('base64url');
  await db.update(users).set({ passwordHash: await hashPassword(password) }).where(eq(users.id, id));
  await revokeSessions(id);

  return ok({ username: user.username, password });
}
