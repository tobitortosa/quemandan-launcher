import { createHash } from 'node:crypto';
import { fail, ok, requireAdmin } from '@/lib/api';
import { db } from '@/lib/db';
import { modFiles, packMods } from '@/lib/db/schema';
import { looksLikeJar, looksLikeShaderpack, readJar, readShaderpack } from '@/lib/jar';
import * as modrinth from '@/lib/modrinth';

/** Un .jar de mod no llega ni cerca de esto; el límite es para cortar subidas absurdas. */
const MAX_BYTES = 64 * 1024 * 1024;

/**
 * Subir uno o varios .jar. El admin elige los archivos y el backend se encarga del resto:
 * calcula los hashes, guarda el archivo y averigua el nombre, la versión y si el mod es de
 * cliente o de servidor. Primero le pregunta a Modrinth por el hash; si no lo conoce, lee
 * la ficha que el propio .jar lleva adentro.
 */
export async function POST(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return fail('No llegaron archivos.');
  }

  const uploads = form.getAll('files').filter((entry): entry is File => entry instanceof File);
  if (uploads.length === 0) return fail('No llegaron archivos.');

  const added: unknown[] = [];
  const rejected: { filename: string; reason: string }[] = [];

  for (const upload of uploads) {
    const esShader = looksLikeShaderpack(upload.name);
    if (!looksLikeJar(upload.name) && !esShader) {
      rejected.push({ filename: upload.name, reason: 'No es un mod (.jar) ni un shaderpack (.zip).' });
      continue;
    }
    if (upload.size > MAX_BYTES) {
      rejected.push({ filename: upload.name, reason: 'El archivo es demasiado grande.' });
      continue;
    }

    const bytes = new Uint8Array(await upload.arrayBuffer());
    const buffer = Buffer.from(bytes);
    const sha1 = createHash('sha1').update(buffer).digest('hex');
    const sha512 = createHash('sha512').update(buffer).digest('hex');

    const inside = esShader ? readShaderpack(bytes, upload.name) : readJar(bytes);
    if (!inside) {
      rejected.push({
        filename: upload.name,
        reason: esShader
          ? 'No parece un shaderpack: no tiene una carpeta shaders adentro.'
          : 'No parece un mod de Fabric: no tiene fabric.mod.json adentro.',
      });
      continue;
    }

    // Si Modrinth reconoce el archivo, se usa su información, que es más completa.
    const known = esShader ? null : await modrinth.byHash(sha1).catch(() => null);
    let title = inside.name || upload.name;
    let versionNumber = inside.version;
    let side: string = inside.side;
    let license = inside.license;
    let pageUrl = '';
    let projectId = `jar:${inside.id || sha1.slice(0, 12)}`;
    let versionId = `sha1:${sha1}`;

    if (known) {
      try {
        const project = await modrinth.project(known.project_id);
        title = project.title;
        side = modrinth.sideOf(project);
        license = project.license.id;
        pageUrl = `https://modrinth.com/${project.project_type}/${project.slug}`;
        projectId = project.id;
      } catch {
        // Si falla, quedan los datos que trae el .jar.
      }
      versionNumber = known.version_number;
      versionId = known.id;
    }

    await db
      .insert(modFiles)
      .values({ sha1, filename: upload.name, size: buffer.byteLength, data: buffer })
      .onConflictDoNothing();

    const row = {
      projectId,
      slug: inside.id || sha1.slice(0, 12),
      title,
      versionId,
      versionNumber,
      filename: upload.name,
      url: `/api/files/${sha1}`,
      sha1,
      sha512,
      size: buffer.byteLength,
      side,
      license,
      pageUrl,
      requires: [],
      source: 'upload',
      kind: esShader ? 'shader' : 'mod',
    };

    await db.insert(packMods).values(row).onConflictDoUpdate({ target: packMods.projectId, set: row });

    added.push({
      title: row.title,
      version: row.versionNumber,
      filename: row.filename,
      side: row.side,
      license: row.license,
      recognised: Boolean(known),
      sizeKb: Math.round(row.size / 1024),
      note: esShader
        ? `${row.title} queda disponible en el menú de shaders del juego.`
        : row.side !== 'client'
          ? `${row.filename} también va en el servidor.`
          : null,
    });
  }

  return ok({ added, rejected });
}
