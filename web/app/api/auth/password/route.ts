import { eq } from 'drizzle-orm';
import { z } from 'zod';
import { fail, ok, readJson, requireUser } from '@/lib/api';
import { hashPassword } from '@/lib/auth';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { env } from '@/lib/env';

const Body = z.object({
  password: z.string(),
  confirm: z.string(),
});

/**
 * La persona elige su propia contraseña. Se usa después de que el administrador se la
 * restablece: entra con la provisoria y lo primero que hace es poner la suya, que el
 * administrador no conoce.
 */
export async function POST(request: Request) {
  const guard = await requireUser(request);
  if ('response' in guard) return guard.response;

  const parsed = Body.safeParse(await readJson<unknown>(request));
  if (!parsed.success) return fail('Faltan las dos contraseñas.');

  const { password, confirm } = parsed.data;

  if (password !== confirm) return fail('Las dos contraseñas no coinciden.');
  if (password.length < 6) return fail('La contraseña necesita al menos 6 caracteres.');
  if (password === env.defaultPassword) {
    return fail('Esa es la contraseña provisoria. Elegí una tuya.');
  }

  await db
    .update(users)
    .set({ passwordHash: await hashPassword(password), mustChangePassword: false })
    .where(eq(users.id, guard.user.id));

  return ok({ ok: true });
}
