import { fail, ok, requireAdmin } from '@/lib/api';
import * as modrinth from '@/lib/modrinth';

/** Busca mods en Modrinth ya filtrados por la versión y el loader del pack. */
export async function GET(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const query = new URL(request.url).searchParams.get('q')?.trim();
  if (!query) return ok({ hits: [] });

  try {
    return ok({ hits: await modrinth.search(query) });
  } catch {
    return fail('No pude buscar en Modrinth en este momento.', 502);
  }
}
