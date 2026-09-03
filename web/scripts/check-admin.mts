/** Llama a las rutas de admin con una sesión recién creada, para ver qué devuelven. */
import { eq } from 'drizzle-orm';
import { createSession } from '../lib/auth';
import { db } from '../lib/db';
import { users } from '../lib/db/schema';

const admin = (await db.select().from(users).where(eq(users.role, 'admin')).limit(1))[0];
const token = await createSession(admin.id);

const mods = (await import('../app/api/admin/mods/route')).GET;
const response = await mods(new Request('http://local/api/admin/mods', {
  headers: { Authorization: `Bearer ${token}` },
}));
const body = (await response.json()) as {
  publishedVersion?: string; hasUnpublishedChanges?: boolean;
  mods?: { title: string; versionNumber: string; side: string }[]; error?: string;
};

console.log('status', response.status);
if (body.error) console.log('error:', body.error);
else {
  console.log('versión publicada:', body.publishedVersion, '· cambios sin publicar:', body.hasUnpublishedChanges);
  console.log('mods:', body.mods?.length);
  for (const m of body.mods?.slice(0, 4) ?? []) console.log('  ', m.title, m.versionNumber, m.side);
}
process.exit(0);
