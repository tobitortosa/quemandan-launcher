/**
 * Reescribe la whitelist del servidor a partir de las cuentas activas.
 *   npm run whitelist
 */
import { syncWhitelist, offlineUuid } from '../lib/whitelist';

const result = await syncWhitelist();
console.log(`whitelist reescrita con ${result.count} jugadores:`);
for (const name of result.names) console.log(`  ${name.padEnd(16)} ${offlineUuid(name)}`);
process.exit(0);
