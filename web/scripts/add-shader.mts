/**
 * Agrega un shaderpack al pack desde su página de Modrinth.
 *   npm run pack:shader -- complementary-unbound
 *
 * Va por Modrinth y no por archivo a propósito: la licencia de Complementary no
 * permite volver a publicar el zip en otro lado, pero sí enlazarlo desde ahí.
 */
import { eq } from 'drizzle-orm';
import { createSession } from '../lib/auth';
import { db } from '../lib/db';
import { users } from '../lib/db/schema';

const reference = process.argv[2];
if (!reference) {
  console.log('Falta el shaderpack. Ejemplo: npm run pack:shader -- complementary-unbound');
  process.exit(1);
}

const admin = (await db.select().from(users).where(eq(users.role, 'admin')).limit(1))[0];
const token = await createSession(admin.id);

const add = (await import('../app/api/admin/mods/route')).POST;
const response = await add(
  new Request('http://local/api/admin/mods', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ reference }),
  }),
);

const body = (await response.json()) as {
  mod?: { title: string; versionNumber: string; filename: string; kind: string; license: string };
  note?: string;
  error?: string;
};

if (body.error) {
  console.log('No se pudo:', body.error);
  process.exit(1);
}

const m = body.mod!;
console.log(`agregado: ${m.title} ${m.versionNumber}`);
console.log(`  archivo: ${m.filename}`);
console.log(`  tipo: ${m.kind} · licencia: ${m.license}`);
if (body.note) console.log(`  ${body.note}`);
process.exit(0);
