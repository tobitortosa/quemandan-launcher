/** Muestra el pack publicado tal como lo recibe el launcher. npm run pack:check */
import { latestRelease } from '../lib/pack';

const release = await latestRelease();
if (!release) {
  console.log('todavía no hay ninguna versión publicada');
} else {
  const p = release.content;
  console.log(`pack ${p.packVersion} · Minecraft ${p.minecraft} · Fabric ${p.fabricLoader}`);
  console.log(`servidor: ${p.server.name} (${p.server.address})`);
  console.log(`${p.mods.length} mods`);
}
process.exit(0);
