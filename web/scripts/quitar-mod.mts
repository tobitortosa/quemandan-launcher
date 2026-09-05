/**
 * Saca un mod del pack y publica la versión nueva.
 *   npm run pack:quitar -- mr_player_revive
 *
 * Es el inverso de pack:jar. Se pasa el slug tal como sale en pack:check.
 */
import { eq } from 'drizzle-orm';
import { createSession } from '../lib/auth';
import { db } from '../lib/db';
import { users } from '../lib/db/schema';
import { latestRelease } from '../lib/pack';

const slug = process.argv[2];
if (!slug) {
  console.log('Falta el slug. Ejemplo: npm run pack:quitar -- mr_player_revive');
  process.exit(1);
}

const release = await latestRelease();
const mod = release?.content.mods.find((m) => m.slug === slug);
if (!mod) {
  console.log(`No hay ningún "${slug}" en el pack publicado.`);
  process.exit(1);
}
console.log(`sacando ${mod.slug} ${mod.versionNumber} (${mod.filename})`);

const admins = await db.select().from(users).where(eq(users.role, 'admin')).limit(1);
if (admins.length === 0) {
  console.log('No hay ninguna cuenta de administrador.');
  process.exit(1);
}
const headers = { Authorization: `Bearer ${await createSession(admins[0].id)}` };

const quitar = (await import('../app/api/admin/mods/route')).DELETE;
const borrado = await (
  await quitar(
    new Request(`http://local/api/admin/mods?projectId=${encodeURIComponent(mod.projectId)}`, {
      method: 'DELETE',
      headers,
    }),
  )
).json();
if (!borrado.removed) {
  console.log('No se pudo quitar:', JSON.stringify(borrado));
  process.exit(1);
}

const publicar = (await import('../app/api/admin/pack/publish/route')).POST;
const nuevo = (await (
  await publicar(new Request('http://local/api/admin/pack/publish', { method: 'POST', headers }))
).json()) as { version?: string; mods?: number; error?: string; problems?: string[] };

if (!nuevo.version) {
  console.log(`No se publicó: ${nuevo.error}`);
  for (const problema of nuevo.problems ?? []) console.log(`  - ${problema}`);
  process.exit(1);
}
console.log(`Pack ${nuevo.version} publicado con ${nuevo.mods} mods.`);
process.exit(0);
