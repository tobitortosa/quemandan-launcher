/** Muestra las cuentas y su estado. npm run users */
import { db } from '../lib/db';
import { users } from '../lib/db/schema';

const rows = await db
  .select({ u: users.username, s: users.status, r: users.role, m: users.mustChangePassword })
  .from(users);

for (const row of rows) {
  console.log(
    `  ${row.u.padEnd(16)} ${row.s.padEnd(8)} ${row.r.padEnd(7)} ${row.m ? 'tiene que elegir contraseña' : ''}`,
  );
}
process.exit(0);
