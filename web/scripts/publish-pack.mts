/**
 * Sube los .jar de una carpeta al pack y publica una versión nueva.
 * Es la misma cosa que va a hacer el botón del panel de admin; hasta que exista la
 * pantalla, sirve para dejar el pack listo desde la consola.
 *
 *   npm run pack:publish -- "C:/Users/Tobi/AppData/Roaming/.minecraft/mods"
 *   npm run pack:publish -- <carpeta> --excluir maplink,otro
 *   npm run pack:publish -- <carpeta> --solo-subir      (sube y no publica)
 */
import { readFileSync, readdirSync } from 'node:fs';
import { basename, join } from 'node:path';
import { eq } from 'drizzle-orm';
import { db } from '../lib/db';
import { packMods, users } from '../lib/db/schema';
import { createSession } from '../lib/auth';

const folder = process.argv[2];
if (!folder) {
  console.log('Falta la carpeta con los .jar.');
  process.exit(1);
}

const excludeArg = process.argv.indexOf('--excluir');
const excluded = excludeArg > 0 ? (process.argv[excludeArg + 1] ?? '').split(',').filter(Boolean) : [];
const onlyUpload = process.argv.includes('--solo-subir');

// Se necesita una sesión de administrador: las rutas verifican el rol.
const admins = await db.select().from(users).where(eq(users.role, 'admin')).limit(1);
if (admins.length === 0) {
  console.log('No hay ninguna cuenta de administrador. Corré primero npm run db:seed.');
  process.exit(1);
}
const token = await createSession(admins[0].id);

const upload = (await import('../app/api/admin/mods/upload/route')).POST;
const publish = (await import('../app/api/admin/pack/publish/route')).POST;
const mods = await import('../app/api/admin/mods/route');

const jars = readdirSync(folder)
  .filter((f) => f.endsWith('.jar'))
  .filter((f) => !excluded.some((e) => f.toLowerCase().includes(e.toLowerCase())));

if (jars.length === 0) {
  console.log(`No encontré .jar en ${folder}.`);
  process.exit(1);
}

console.log(`Subiendo ${jars.length} archivos de ${folder}`);
if (excluded.length > 0) console.log(`Excluidos: ${excluded.join(', ')}`);

const form = new FormData();
for (const name of jars) {
  const bytes = readFileSync(join(folder, name));
  form.append('files', new File([new Uint8Array(bytes)], basename(name), { type: 'application/java-archive' }));
}

const uploadResponse = await upload(
  new Request('http://local/api/admin/mods/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  }),
);

const uploaded = (await uploadResponse.json()) as {
  added: { title: string; version: string; side: string; recognised: boolean; sizeKb: number; license: string }[];
  rejected: { filename: string; reason: string }[];
  error?: string;
};

if (uploaded.error) {
  console.log('Error:', uploaded.error);
  process.exit(1);
}

for (const mod of uploaded.added) {
  const origin = mod.recognised ? 'Modrinth' : 'del jar';
  console.log(
    `  ${mod.title.slice(0, 26).padEnd(26)} ${mod.version.slice(0, 22).padEnd(22)} ` +
      `${mod.side.padEnd(6)} ${String(mod.sizeKb).padStart(6)} KB  ${origin}  ${mod.license}`,
  );
}
for (const bad of uploaded.rejected) console.log(`  RECHAZADO ${bad.filename}: ${bad.reason}`);

// Quitar del pack los mods que ya no están en la carpeta.
const wanted = new Set(jars);
const current = await db.select().from(packMods);
for (const mod of current) {
  if (!wanted.has(mod.filename)) {
    await mods.DELETE(
      new Request(`http://local/api/admin/mods?projectId=${encodeURIComponent(mod.projectId)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
    console.log(`  quitado ${mod.filename} (ya no está en la carpeta)`);
  }
}

if (onlyUpload) {
  console.log('\nListo, sin publicar (--solo-subir).');
  process.exit(0);
}

const publishResponse = await publish(
  new Request('http://local/api/admin/pack/publish', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  }),
);
const release = (await publishResponse.json()) as {
  version?: string;
  mods?: number;
  serverSide?: string[];
  error?: string;
  problems?: string[];
};

if (!release.version) {
  console.log(`\nNo se publicó: ${release.error}`);
  for (const problem of release.problems ?? []) console.log(`  - ${problem}`);
  process.exit(1);
}

console.log(`\nPack ${release.version} publicado con ${release.mods} mods.`);
if (release.serverSide?.length) {
  console.log('\nEstos también van en el servidor (subilos por SFTP a /mods):');
  for (const file of release.serverSide) console.log(`  ${file}`);
}
process.exit(0);
