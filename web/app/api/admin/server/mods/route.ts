import { inArray } from 'drizzle-orm';
import { z } from 'zod';
import { fail, ok, pterodactylFailure, readJson, requireAdmin } from '@/lib/api';
import { db } from '@/lib/db';
import { modFiles, packMods } from '@/lib/db/schema';
import { deleteFiles, listFiles, uploadFile } from '@/lib/pterodactyl';

const MODS_DIR = '/mods';

/** Los mods del pack que además van en el servidor. */
async function serverSide() {
  const mods = await db.select().from(packMods);
  return mods.filter((m) => m.side === 'server' || m.side === 'both');
}

/**
 * Compara la carpeta de mods del servidor con lo que dice el pack.
 * Es solo lectura: no cambia nada.
 */
export async function GET(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const wanted = await serverSide();

  let present: string[];
  try {
    present = (await listFiles(MODS_DIR)).filter((f) => f.isFile && f.name.endsWith('.jar')).map((f) => f.name);
  } catch (error) {
    return pterodactylFailure(error, 'Leer los mods del servidor');
  }

  const expected = new Set(wanted.map((m) => m.filename));

  return ok({
    directory: MODS_DIR,
    /** Están en el pack pero no en el servidor: hay que subirlos. */
    missing: wanted.filter((m) => !present.includes(m.filename)).map((m) => ({
      filename: m.filename,
      title: m.title,
      version: m.versionNumber,
      size: m.size,
    })),
    /** Están en el servidor pero no en el pack. */
    extra: present.filter((name) => !expected.has(name)),
    /** Coinciden. */
    ok: present.filter((name) => expected.has(name)),
  });
}

const Body = z.object({
  /** Subir al servidor los mods del pack que falten. */
  upload: z.boolean().optional(),
  /** Nombres de archivo a borrar del servidor. Se pasan explícitos a propósito. */
  remove: z.array(z.string()).optional(),
});

/**
 * Aplica los cambios en la carpeta de mods del servidor.
 * Borrar se pide por nombre, uno por uno: nadie borra archivos del servidor sin
 * haberlos visto en la lista.
 */
export async function POST(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const parsed = Body.safeParse(await readJson<unknown>(request));
  if (!parsed.success) return fail('No entendí qué hacer.');

  const { upload = false, remove = [] } = parsed.data;
  const uploaded: string[] = [];
  const removed: string[] = [];

  try {
    if (upload) {
      const wanted = await serverSide();
      const present = (await listFiles(MODS_DIR)).filter((f) => f.isFile).map((f) => f.name);
      const missing = wanted.filter((m) => !present.includes(m.filename));

      // Los archivos propios salen de la base; los que apuntan a Modrinth se bajan
      // en el momento y se reenvían al servidor.
      const own = missing.filter((m) => m.source === 'upload').map((m) => m.sha1);
      const stored = own.length
        ? new Map(
            (await db.select().from(modFiles).where(inArray(modFiles.sha1, own))).map((f) => [f.sha1, f.data]),
          )
        : new Map<string, Buffer>();

      for (const mod of missing) {
        const bytes = stored.get(mod.sha1);
        if (bytes) {
          await uploadFile(MODS_DIR, mod.filename, new Uint8Array(bytes));
        } else {
          const response = await fetch(mod.url);
          if (!response.ok) throw new Error(`No pude descargar ${mod.filename} para reenviarlo.`);
          await uploadFile(MODS_DIR, mod.filename, new Uint8Array(await response.arrayBuffer()));
        }
        uploaded.push(mod.filename);
      }
    }

    if (remove.length > 0) {
      const safe = remove.filter((name) => name.endsWith('.jar') && !name.includes('/') && !name.includes('..'));
      await deleteFiles(MODS_DIR, safe);
      removed.push(...safe);
    }
  } catch (error) {
    return pterodactylFailure(error, 'Cambiar los mods del servidor');
  }

  return ok({
    uploaded,
    removed,
    note:
      uploaded.length > 0 || removed.length > 0
        ? 'Reiniciá el servidor para que los cambios tengan efecto.'
        : 'No hubo nada que cambiar.',
  });
}
