import { env } from './env';

/**
 * Cliente del panel de Minehost. La clave da control total del servidor
 * (consola, archivos, apagarlo), así que vive únicamente acá, en el backend.
 * El launcher nunca la ve ni conoce la URL del panel.
 */
export class PterodactylError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly serverOffline: boolean,
  ) {
    super(message);
  }
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(`${env.pterodactylUrl}/api/client${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.pterodactylKey}`,
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...init?.headers,
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    // 502 y 412 son la forma que tiene el panel de decir "el servidor está apagado".
    const offline = response.status === 502 || response.status === 412;
    throw new PterodactylError(
      offline
        ? 'El servidor de Minecraft está apagado.'
        : `El panel respondió ${response.status}.`,
      response.status,
      offline,
    );
  }

  return response;
}

/** Ejecuta un comando en la consola del servidor. */
export async function runCommand(command: string): Promise<void> {
  await request(`/servers/${env.pterodactylServerId}/command`, {
    method: 'POST',
    body: JSON.stringify({ command }),
  });
}

export async function serverState(): Promise<{ state: string; online: boolean }> {
  const response = await request(`/servers/${env.pterodactylServerId}/resources`);
  const body = (await response.json()) as { attributes?: { current_state?: string } };
  const state = body.attributes?.current_state ?? 'unknown';
  return { state, online: state === 'running' };
}

export const whitelist = {
  add: (username: string) => runCommand(`whitelist add ${username}`),
  remove: (username: string) => runCommand(`whitelist remove ${username}`),
};

export const kick = (username: string, reason: string) =>
  runCommand(`kick ${username} ${reason}`);
