/**
 * Crea (o actualiza) la cuenta de administrador y las cuentas de los jugadores que ya
 * están en el servidor.
 *
 * Tu contraseña la elegís vos en .env.local:
 *
 *   ADMIN_USERNAME=PEPE
 *   ADMIN_PASSWORD=la-que-quieras
 *
 * Si ADMIN_PASSWORD está puesta, este script la aplica cada vez que corre. Así podés
 * cambiarla cuando quieras sin que nadie más la vea: el archivo es local y no se sube
 * al repositorio.
 *
 * Los jugadores reciben una contraseña al azar la primera vez, y el script la imprime
 * para que se la pases.
 *
 *   npm run db:seed
 */
import { eq } from 'drizzle-orm';
import { hashPassword, revokeSessions } from '../lib/auth';
import { db } from '../lib/db';
import { users } from '../lib/db/schema';
import { env } from '../lib/env';
import { isValidUsername, normalize, USERNAME_RULE } from '../lib/username';

const ADMIN = process.env.ADMIN_USERNAME?.trim() || 'PEPE';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD?.trim();
const PLAYERS = (process.env.PLAYERS?.trim() || 'Chichon,Titit0N,Luquitas1410,Felix_1256')
  .split(',')
  .map((name) => name.trim())
  .filter(Boolean);

if (!isValidUsername(ADMIN)) {
  console.log(`ADMIN_USERNAME "${ADMIN}" no sirve. ${USERNAME_RULE}`);
  process.exit(1);
}

if (ADMIN_PASSWORD && ADMIN_PASSWORD.length < 6) {
  console.log('ADMIN_PASSWORD necesita al menos 6 caracteres.');
  process.exit(1);
}

async function findByName(username: string) {
  const rows = await db.select().from(users).where(eq(users.usernameLower, normalize(username))).limit(1);
  return rows[0];
}

// ---- Administrador
{
  const existing = await findByName(ADMIN);

  if (!existing) {
    const password = ADMIN_PASSWORD ?? env.defaultPassword;
    await db.insert(users).values({
      username: ADMIN,
      usernameLower: normalize(ADMIN),
      passwordHash: await hashPassword(password),
      role: 'admin',
      status: 'active',
      approvedAt: new Date(),
    });
    console.log(
      ADMIN_PASSWORD
        ? `creada       ${ADMIN.padEnd(14)} rol admin  con la contraseña de tu .env.local`
        : `creada       ${ADMIN.padEnd(14)} rol admin  entra con: ${password}`,
    );
  } else if (ADMIN_PASSWORD) {
    await db
      .update(users)
      .set({ passwordHash: await hashPassword(ADMIN_PASSWORD), role: 'admin', status: 'active' })
      .where(eq(users.id, existing.id));
    await revokeSessions(existing.id);
    console.log(`actualizada  ${ADMIN.padEnd(14)} rol admin  contraseña puesta desde tu .env.local`);
  } else {
    console.log(`ya existía   ${ADMIN.padEnd(14)} (poné ADMIN_PASSWORD en .env.local para cambiarla)`);
  }
}

// ---- Jugadores que ya están en el servidor
for (const player of PLAYERS) {
  if (!isValidUsername(player)) {
    console.log(`omitido      ${player} (nombre inválido)`);
    continue;
  }

  if (await findByName(player)) {
    console.log(`ya existía   ${player}`);
    continue;
  }

  await db.insert(users).values({
    username: player,
    usernameLower: normalize(player),
    passwordHash: await hashPassword(env.defaultPassword),
    role: 'player',
    status: 'active',
    approvedAt: new Date(),
    mustChangePassword: true,
  });
  console.log(`creada       ${player.padEnd(14)} rol player entra con: ${env.defaultPassword}`);
}

console.log('\nOjo: los nombres respetan mayúsculas y no se pueden cambiar: son la identidad');
console.log('de cada jugador en el servidor, y de ahí sale su inventario.');
process.exit(0);
