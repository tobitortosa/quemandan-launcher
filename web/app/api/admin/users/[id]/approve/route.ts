import { eq } from 'drizzle-orm';
import { fail, ok, pterodactylFailure, requireAdmin } from '@/lib/api';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { syncWhitelist } from '@/lib/whitelist';

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const id = Number.parseInt((await context.params).id, 10);
  if (!Number.isFinite(id)) return fail('Id de usuario inválido.');

  const rows = await db.select().from(users).where(eq(users.id, id)).limit(1);
  const user = rows[0];
  if (!user) return fail('Esa cuenta no existe.', 404);
  if (user.status === 'active') return ok({ username: user.username, status: 'active' });

  // La whitelist del servidor se arma a partir de las cuentas activas, así que primero
  // se cambia la cuenta y después se escribe el archivo. Si el servidor no responde,
  // se deshace el cambio: nunca queda una cuenta aprobada que el servidor rechaza.
  await db
    .update(users)
    .set({ status: 'active', approvedAt: new Date(), bannedAt: null })
    .where(eq(users.id, id));

  try {
    await syncWhitelist();
  } catch (error) {
    await db.update(users).set({ status: user.status, approvedAt: user.approvedAt }).where(eq(users.id, id));
    return pterodactylFailure(error, `Aprobar a ${user.username}`);
  }

  return ok({ username: user.username, status: 'active' });
}
