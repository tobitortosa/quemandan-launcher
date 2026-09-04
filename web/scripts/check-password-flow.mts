/** Comprueba de punta a punta el circuito de la contraseña provisoria. */
import { eq } from 'drizzle-orm';
import { createSession } from '../lib/auth';
import { db } from '../lib/db';
import { users } from '../lib/db/schema';
import { env } from '../lib/env';

const NOMBRE = process.argv[2] ?? 'usuarioprueba';
const NUEVA = 'la-mia-secreta-123';

const admin = (await db.select().from(users).where(eq(users.role, 'admin')).limit(1))[0];
const target = (await db.select().from(users).where(eq(users.username, NOMBRE)).limit(1))[0];
if (!target) { console.log('no existe', NOMBRE); process.exit(1); }

const adminToken = await createSession(admin.id);
const reset = (await import('../app/api/admin/users/[id]/password/route')).POST;
const login = (await import('../app/api/auth/login/route')).POST;
const change = (await import('../app/api/auth/password/route')).POST;

const post = (url: string, body?: unknown, token?: string) =>
  new Request(`http://local${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

let ok = 0;
const fallas: string[] = [];
const check = (name: string, cond: boolean, extra = '') => {
  if (cond) { ok++; console.log(`  ok    ${name}`); }
  else { fallas.push(name); console.log(`  FALLA ${name} ${extra}`); }
};

// 1. El administrador restablece
let r = await reset(post(`/api/admin/users/${target.id}/password`, undefined, adminToken), {
  params: Promise.resolve({ id: String(target.id) }),
});
const restablecida = (await r.json()) as { password: string };
check('restablecer devuelve la provisoria', restablecida.password === env.defaultPassword, restablecida.password);

// 2. Entra con la provisoria y le piden cambiarla
r = await login(post('/api/auth/login', { username: NOMBRE, password: env.defaultPassword }));
const entrada = (await r.json()) as { token: string; user: { mustChangePassword: boolean } };
check('entra con la provisoria', r.status === 200);
check('le pide elegir una propia', entrada.user?.mustChangePassword === true);

// 3. No puede repetir la provisoria
r = await change(post('/api/auth/password', { password: env.defaultPassword, confirm: env.defaultPassword }, entrada.token));
check('no la deja dejar la provisoria', r.status === 400);

// 4. Ni poner dos distintas
r = await change(post('/api/auth/password', { password: NUEVA, confirm: 'otra-cosa' }, entrada.token));
check('exige que las dos coincidan', r.status === 400);

// 5. Elige la suya
r = await change(post('/api/auth/password', { password: NUEVA, confirm: NUEVA }, entrada.token));
check('acepta la contraseña nueva', r.status === 200);

// 6. Entra con la suya y ya no le piden nada
r = await login(post('/api/auth/login', { username: NOMBRE, password: NUEVA }));
const despues = (await r.json()) as { user: { mustChangePassword: boolean } };
check('entra con la suya', r.status === 200);
check('ya no le piden cambiarla', despues.user?.mustChangePassword === false);

// 7. La provisoria dejó de servir
r = await login(post('/api/auth/login', { username: NOMBRE, password: env.defaultPassword }));
check('la provisoria ya no sirve', r.status === 401);

console.log(`\n${ok} comprobaciones pasaron, ${fallas.length} fallaron.`);
process.exit(fallas.length === 0 ? 0 : 1);
