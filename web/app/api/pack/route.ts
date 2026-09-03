import { fail, ok, requireActiveUser } from '@/lib/api';
import { latestRelease } from '@/lib/pack';

/**
 * El pack que tiene que instalar el launcher. Solo para cuentas aprobadas:
 * una cuenta pendiente no descarga nada.
 */
export async function GET(request: Request) {
  const guard = await requireActiveUser(request);
  if ('response' in guard) return guard.response;

  const release = await latestRelease();
  if (!release) return fail('Todavía no hay ninguna versión del pack publicada.', 404);

  // Los archivos que subió el admin se guardan con una ruta relativa; el launcher
  // necesita la dirección completa para poder descargarlos.
  const origin = new URL(request.url).origin;
  const content = {
    ...release.content,
    mods: release.content.mods.map((mod) => ({
      ...mod,
      url: mod.url.startsWith('/') ? `${origin}${mod.url}` : mod.url,
    })),
  };

  return ok(content);
}
