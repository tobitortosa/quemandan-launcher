import { unzipSync } from 'fflate';

/**
 * Lee la ficha que todo mod de Fabric lleva adentro (`fabric.mod.json`).
 * Sirve para saber el nombre, la versión y si el mod es de cliente o de servidor
 * cuando el archivo no está en Modrinth.
 */
export type JarInfo = {
  id: string;
  name: string;
  version: string;
  /** "client", "server" o "both". */
  side: 'client' | 'server' | 'both';
  license: string;
  /** Los mods que declara como obligatorios, por su id de Fabric. */
  depends: string[];
};

type FabricModJson = {
  id?: string;
  name?: string;
  version?: string;
  environment?: string;
  license?: string | string[];
  depends?: Record<string, unknown>;
};

export function readJar(bytes: Uint8Array): JarInfo | null {
  let entries: Record<string, Uint8Array>;
  try {
    entries = unzipSync(bytes, { filter: (file) => file.name === 'fabric.mod.json' });
  } catch {
    return null;
  }

  const raw = entries['fabric.mod.json'];
  if (!raw) return null;

  let parsed: FabricModJson;
  try {
    parsed = JSON.parse(new TextDecoder().decode(raw)) as FabricModJson;
  } catch {
    return null;
  }

  const environment = parsed.environment ?? '*';
  const side = environment === 'client' ? 'client' : environment === 'server' ? 'server' : 'both';

  const license = Array.isArray(parsed.license) ? parsed.license.join(', ') : (parsed.license ?? '');

  // Los ids propios de Fabric y de Minecraft no cuentan como dependencias del pack.
  const ignored = new Set(['fabricloader', 'minecraft', 'java', 'fabric-api-base']);
  const depends = Object.keys(parsed.depends ?? {}).filter((id) => !ignored.has(id));

  return {
    id: parsed.id ?? '',
    name: parsed.name ?? parsed.id ?? '',
    version: parsed.version ?? '',
    side,
    license,
    depends,
  };
}

export function looksLikeJar(filename: string): boolean {
  return filename.toLowerCase().endsWith('.jar');
}

export function looksLikeZip(filename: string): boolean {
  return filename.toLowerCase().endsWith('.zip');
}

/**
 * Un paquete de recursos es un .zip con pack.mcmeta en la raíz. Se distingue de un
 * shaderpack, que en cambio tiene una carpeta "shaders".
 */
export function readResourcePack(bytes: Uint8Array, filename: string): JarInfo | null {
  let names: string[];
  try {
    names = Object.keys(unzipSync(bytes, { filter: (file) => file.name === 'pack.mcmeta' }));
  } catch {
    return null;
  }

  if (names.length === 0) return null;
  return describeZip(filename);
}

/**
 * Un shaderpack es un .zip con una carpeta "shaders" adentro. No trae ficha con su
 * nombre ni su versión, así que se toman del nombre del archivo, que es la convención
 * que usan todos: ComplementaryUnbound_r5.8.1.zip
 */
export function readShaderpack(bytes: Uint8Array, filename: string): JarInfo | null {
  let names: string[];
  try {
    names = Object.keys(unzipSync(bytes, { filter: (file) => file.name.includes('shaders/') }));
  } catch {
    return null;
  }

  if (names.length === 0) return null;
  return describeZip(filename);
}

/**
 * Ni los shaderpacks ni los paquetes de recursos traen una ficha con su nombre y su
 * versión, así que se toman del nombre del archivo, que es la convención que usan
 * todos: ComplementaryUnbound_r5.8.1.zip
 */
function describeZip(filename: string): JarInfo {
  const base = filename.replace(/\.zip$/i, '');
  const match = base.match(/^(.*?)[_ -]?(v?\.?\s*[\d][\w.]*)$/);

  return {
    id: base,
    name: (match?.[1] ?? base).replace(/[_-]+/g, ' ').trim(),
    version: (match?.[2] ?? '').trim(),
    side: 'client',
    license: '',
    depends: [],
  };
}
