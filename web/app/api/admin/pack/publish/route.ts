import { fail, ok, requireAdmin } from '@/lib/api';
import { db } from '@/lib/db';
import { packReleases } from '@/lib/db/schema';
import { draftMods, latestRelease, nextVersion, serverSideMods, toPayload, validate } from '@/lib/pack';

/**
 * Publica el pack. Antes revisa que no falte una dependencia obligatoria y que las
 * descargas sigan existiendo: si algo está mal, no publica y dice qué pasa.
 * Un pack roto se traduce en un crash al arrancar que el jugador no puede diagnosticar.
 */
export async function POST(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const mods = await draftMods();
  if (mods.length === 0) return fail('El pack está vacío: agregá al menos un mod.');

  const problems = await validate(mods);
  if (problems.length > 0) {
    return fail('No se publicó nada porque el pack tiene problemas.', 409, {
      problems: problems.map((p) => p.detail),
    });
  }

  const current = await latestRelease();
  const version = nextVersion(current?.version ?? null);
  const content = toPayload(mods, version);

  await db.insert(packReleases).values({ version, content });

  return ok({
    version,
    mods: content.mods.length,
    serverSide: serverSideMods(mods).map((m) => m.filename),
  });
}
