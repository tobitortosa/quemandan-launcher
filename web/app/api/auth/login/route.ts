import { eq } from 'drizzle-orm';
import { z } from 'zod';
import { fail, ok, readJson } from '@/lib/api';
import { checkPassword, createSession } from '@/lib/auth';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { normalize } from '@/lib/username';

const Body = z.object({ username: z.string(), password: z.string() });

export async function POST(request: Request) {
  const parsed = Body.safeParse(await readJson<unknown>(request));
  if (!parsed.success) return fail('Faltan el usuario o la contraseña.');

  const rows = await db
    .select()
    .from(users)
    .where(eq(users.usernameLower, normalize(parsed.data.username)))
    .limit(1);

  const user = rows[0];
  // El mismo mensaje para usuario inexistente y contraseña incorrecta.
  const generic = 'Usuario o contraseña incorrectos.';
  if (!user) return fail(generic, 401);
  if (!(await checkPassword(parsed.data.password, user.passwordHash))) return fail(generic, 401);

  if (user.status === 'banned') return fail('Tu cuenta está baneada.', 403, { status: 'banned' });

  const token = await createSession(user.id);
  return ok({
    token,
    user: { username: user.username, status: user.status, role: user.role },
  });
}
