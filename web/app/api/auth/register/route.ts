import { eq } from 'drizzle-orm';
import { z } from 'zod';
import { fail, ok, readJson } from '@/lib/api';
import { createSession, hashPassword } from '@/lib/auth';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { isValidUsername, normalize, USERNAME_RULE } from '@/lib/username';

const Body = z.object({
  username: z.string(),
  password: z.string(),
});

export async function POST(request: Request) {
  const body = await readJson<unknown>(request);
  const parsed = Body.safeParse(body);
  if (!parsed.success) return fail('Faltan el usuario o la contraseña.');

  const { username, password } = parsed.data;

  if (!isValidUsername(username)) return fail(USERNAME_RULE);
  if (password.length < 6) return fail('La contraseña necesita al menos 6 caracteres.');

  const lower = normalize(username);
  const existing = await db.select({ id: users.id }).from(users).where(eq(users.usernameLower, lower)).limit(1);
  if (existing.length > 0) return fail('Ese nombre ya está tomado. Probá con otro.', 409);

  const inserted = await db
    .insert(users)
    .values({ username, usernameLower: lower, passwordHash: await hashPassword(password) })
    .returning({ id: users.id, username: users.username, status: users.status, role: users.role });

  const user = inserted[0];
  const token = await createSession(user.id);

  return ok(
    {
      token,
      user: { username: user.username, status: user.status, role: user.role },
    },
    201,
  );
}
