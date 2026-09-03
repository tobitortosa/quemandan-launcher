import { eq } from 'drizzle-orm';
import { fail, requireActiveUser } from '@/lib/api';
import { db } from '@/lib/db';
import { modFiles } from '@/lib/db/schema';

/**
 * Sirve un .jar que subió el admin. Solo para cuentas aprobadas: el pack no es público.
 * El launcher verifica el hash de lo que baja, así que el nombre del archivo es el hash.
 */
export async function GET(request: Request, context: { params: Promise<{ sha1: string }> }) {
  const guard = await requireActiveUser(request);
  if ('response' in guard) return guard.response;

  const { sha1 } = await context.params;
  if (!/^[0-9a-f]{40}$/.test(sha1)) return fail('Archivo inválido.', 400);

  const rows = await db.select().from(modFiles).where(eq(modFiles.sha1, sha1)).limit(1);
  const file = rows[0];
  if (!file) return fail('Ese archivo ya no está.', 404);

  return new Response(new Uint8Array(file.data), {
    headers: {
      'Content-Type': 'application/java-archive',
      'Content-Length': String(file.size),
      'Content-Disposition': `attachment; filename="${file.filename.replace(/"/g, '')}"`,
      // El contenido de un hash nunca cambia.
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
}
