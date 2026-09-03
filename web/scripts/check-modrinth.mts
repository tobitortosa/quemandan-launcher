/** Comprobación en vivo de la integración con Modrinth. npx tsx scripts/check-modrinth.ts */
import * as modrinth from '../lib/modrinth';

const hits = await modrinth.search('sodium', 3);
console.log('búsqueda "sodium":');
for (const h of hits) console.log(`  ${h.slug.padEnd(24)} ${h.title}`);

for (const ref of ['https://modrinth.com/mod/lithium', 'sodium', 'AANobbMI']) {
  const slug = modrinth.parseReference(ref);
  const project = await modrinth.project(slug);
  const versions = await modrinth.versions(project.id);
  const chosen = versions.find((v) => v.version_type === 'release') ?? versions[0];
  const file = modrinth.primaryFile(chosen);
  console.log(
    `\n${ref}\n  -> ${project.title} (${modrinth.sideOf(project)}, ${project.license.id})` +
      `\n     ${chosen.version_number}  ${file.filename}  ${(file.size / 1024).toFixed(0)} KB` +
      `\n     sha1 ${file.hashes.sha1.slice(0, 12)}…  requiere ${JSON.stringify(modrinth.requiredDependencies(chosen))}`,
  );
}

const iris = await modrinth.project('iris');
const irisVersions = await modrinth.versions(iris.id);
console.log(`\nIris para 26.1: ${irisVersions.length} versiones; la más nueva es ${irisVersions[0]?.version_number}`);
