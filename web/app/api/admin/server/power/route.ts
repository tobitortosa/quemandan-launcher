import { z } from 'zod';
import { fail, ok, pterodactylFailure, readJson, requireAdmin } from '@/lib/api';
import { power } from '@/lib/pterodactyl';

const Body = z.object({ signal: z.enum(['start', 'restart', 'stop']) });

/** Prender, reiniciar o apagar el servidor desde el panel del launcher. */
export async function POST(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const parsed = Body.safeParse(await readJson<unknown>(request));
  if (!parsed.success) return fail('Falta decir qué hacer: prender, reiniciar o apagar.');

  try {
    await power(parsed.data.signal);
  } catch (error) {
    const accion =
      parsed.data.signal === 'start' ? 'Prender' : parsed.data.signal === 'stop' ? 'Apagar' : 'Reiniciar';
    return pterodactylFailure(error, `${accion} el servidor`);
  }

  return ok({ signal: parsed.data.signal });
}
