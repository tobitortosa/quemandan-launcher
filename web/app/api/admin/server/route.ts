import { ok, requireAdmin } from '@/lib/api';
import { PterodactylError, serverState } from '@/lib/pterodactyl';

/** Estado del servidor según el panel, para el panel de admin. */
export async function GET(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  try {
    return ok(await serverState());
  } catch (error) {
    const message =
      error instanceof PterodactylError
        ? error.message
        : 'No se pudo contactar al panel de Minehost.';
    return ok({ state: 'unknown', online: false, error: message });
  }
}
