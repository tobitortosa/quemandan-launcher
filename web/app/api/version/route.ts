import { ok } from '@/lib/api';
import { latestRelease } from '@/lib/pack';

/**
 * El manifiesto que Velopack sube en cada release. Se lee del CDN de GitHub y no
 * de su API a propósito: la API corta a las sesenta consultas por hora y el
 * launcher pregunta cada diez segundos.
 */
const MANIFIESTO =
  'https://github.com/tobitortosa/sobrinosdepepe-launcher/releases/latest/download/releases.win.json';

/** Una respuesta sirve para todos los launchers durante diez segundos. */
export const revalidate = 10;

/**
 * Las dos versiones que tienen que estar al día en la máquina del jugador: la del
 * launcher y la del pack de mods. El launcher las compara con las suyas y, si no
 * coinciden, saca al jugador del juego y actualiza.
 *
 * No pide sesión: es lo único que el launcher consulta seguido y no dice nada que
 * no esté publicado.
 */
export async function GET() {
  const [launcher, pack] = await Promise.all([versionDelLauncher(), latestRelease()]);
  return ok({ launcher, pack: pack?.version ?? null });
}

async function versionDelLauncher(): Promise<string | null> {
  // Si GitHub no contesta se devuelve null y el launcher no molesta a nadie: es
  // preferible a que la pantalla de actualización aparezca por un error de red.
  try {
    const response = await fetch(MANIFIESTO, { next: { revalidate: 10 } });
    if (!response.ok) return null;

    const manifiesto = (await response.json()) as { Assets?: { Version?: string; Type?: string }[] };
    const completo = manifiesto.Assets?.find((a) => a.Type === 'Full') ?? manifiesto.Assets?.[0];
    return completo?.Version ?? null;
  } catch {
    return null;
  }
}
