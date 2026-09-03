import { eq } from 'drizzle-orm';
import { z } from 'zod';
import { fail, ok, readJson, requireAdmin } from '@/lib/api';
import { db } from '@/lib/db';
import { modFiles, packMods } from '@/lib/db/schema';
import { env } from '@/lib/env';
import * as modrinth from '@/lib/modrinth';
import { draftMods, latestRelease, serverSideMods, toPayload } from '@/lib/pack';

/** El pack que está editando el admin, y si difiere de lo último publicado. */
export async function GET(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const draft = await draftMods();
  const release = await latestRelease();
  const draftPayload = toPayload(draft, release?.version ?? '0.0.0');

  const published = release?.content.mods ?? [];
  const publishedKeys = new Set(published.map((m) => `${m.projectId}@${m.versionId}`));
  const draftKeys = new Set(draft.map((m) => `${m.projectId}@${m.versionId}`));
  const changed =
    publishedKeys.size !== draftKeys.size || [...draftKeys].some((k) => !publishedKeys.has(k));

  return ok({
    publishedVersion: release?.version ?? null,
    hasUnpublishedChanges: changed,
    minecraft: env.minecraftVersion,
    fabricLoader: env.fabricLoader,
    mods: draftPayload.mods,
    serverSide: serverSideMods(draft).map((m) => m.filename),
  });
}

const Body = z.object({
  /** Link de Modrinth, slug o id del proyecto. */
  reference: z.string().min(1),
  /** Opcional: una versión concreta. Si no viene, se toma la más nueva compatible. */
  versionId: z.string().optional(),
});

/** Agrega un mod al pack. Los hashes y la URL los resuelve el backend contra Modrinth. */
export async function POST(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const parsed = Body.safeParse(await readJson<unknown>(request));
  if (!parsed.success) return fail('Falta el link o el nombre del mod.');

  const reference = modrinth.parseReference(parsed.data.reference);

  let project: modrinth.ModrinthProject;
  try {
    project = await modrinth.project(reference);
  } catch {
    return fail(`No encontré "${reference}" en Modrinth. Revisá el link.`, 404);
  }

  // Un shaderpack se publica para "iris", no para "fabric".
  const shader = modrinth.isShader(project);
  const loader = shader ? 'iris' : 'fabric';
  const que = shader ? 'shaderpack' : 'mod';

  let version: modrinth.ModrinthVersion | undefined;
  try {
    if (parsed.data.versionId) {
      version = await modrinth.version(parsed.data.versionId);
    } else {
      const list = await modrinth.versions(project.id, loader);
      version = list.find((v) => v.version_type === 'release') ?? list[0];
    }
  } catch {
    return fail(`No pude leer las versiones del ${que} en Modrinth.`, 502);
  }

  if (!version) {
    return fail(
      `${project.title} no tiene ninguna versión para Minecraft ${env.minecraftVersion}.`,
      409,
    );
  }

  if (!version.game_versions.includes(env.minecraftVersion)) {
    return fail(
      `Esa versión de ${project.title} no sirve para Minecraft ${env.minecraftVersion}.`,
      409,
    );
  }

  const file = modrinth.primaryFile(version);

  const row = {
    projectId: project.id,
    slug: project.slug,
    title: project.title,
    versionId: version.id,
    versionNumber: version.version_number,
    filename: file.filename,
    url: file.url,
    sha1: file.hashes.sha1,
    sha512: file.hashes.sha512,
    size: file.size,
    side: shader ? 'client' : modrinth.sideOf(project),
    license: project.license.id,
    pageUrl: `https://modrinth.com/${project.project_type}/${project.slug}`,
    requires: shader ? [] : modrinth.requiredDependencies(version),
    source: 'modrinth',
    kind: shader ? 'shader' : 'mod',
  };

  await db
    .insert(packMods)
    .values(row)
    .onConflictDoUpdate({ target: packMods.projectId, set: row });

  // Avisar en el momento si falta una dependencia o si la que está tiene otra versión.
  const warnings: string[] = [];
  const installed = new Map((await draftMods()).map((m) => [m.projectId, m]));
  for (const dependency of row.requires) {
    const present = installed.get(dependency.projectId);
    const name = await modrinth
      .project(dependency.projectId)
      .then((p) => p.title)
      .catch(() => dependency.projectId);

    if (!present) {
      warnings.push(`Falta ${name}, que ${project.title} necesita para funcionar.`);
    } else if (dependency.versionId && present.versionId !== dependency.versionId) {
      warnings.push(
        `${project.title} ${version.version_number} pide otra versión de ${name}: el pack tiene ${present.versionNumber}.`,
      );
    }
  }

  return ok({
    mod: row,
    warnings,
    note: shader
      ? `${project.title} queda disponible en el menú de shaders del juego. Cada uno lo activa si quiere.`
      : row.side !== 'client'
        ? `${file.filename} también va en el servidor.`
        : null,
  });
}

/** Las versiones disponibles de un mod, para que el admin elija. */
export async function PATCH(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const parsed = z.object({ reference: z.string().min(1) }).safeParse(await readJson<unknown>(request));
  if (!parsed.success) return fail('Falta el mod.');

  try {
    const list = await modrinth.versions(modrinth.parseReference(parsed.data.reference));
    return ok({
      versions: list.map((v) => ({
        versionId: v.id,
        versionNumber: v.version_number,
        type: v.version_type,
        published: v.date_published,
      })),
    });
  } catch {
    return fail('No pude leer las versiones del mod en Modrinth.', 502);
  }
}

export async function DELETE(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const projectId = new URL(request.url).searchParams.get('projectId');
  if (!projectId) return fail('Falta el mod a quitar.');

  const removed = await db
    .delete(packMods)
    .where(eq(packMods.projectId, projectId))
    .returning({ sha1: packMods.sha1, source: packMods.source });

  // Si era un archivo subido y ningún otro mod lo usa, se borra también el archivo.
  for (const mod of removed) {
    if (mod.source !== 'upload') continue;
    const stillUsed = await db
      .select({ id: packMods.id })
      .from(packMods)
      .where(eq(packMods.sha1, mod.sha1))
      .limit(1);
    if (stillUsed.length === 0) await db.delete(modFiles).where(eq(modFiles.sha1, mod.sha1));
  }

  return ok({ removed: projectId });
}
