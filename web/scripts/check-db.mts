/** Comprueba que la base responde. npm run db:check */
import { Pool } from 'pg';
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  connectionTimeoutMillis: 20000,
  ssl: { rejectUnauthorized: true },
});
try {
  const r = await pool.query('select current_database() as db, version() as v');
  console.log('OK ->', r.rows[0].db, '|', String(r.rows[0].v).slice(0, 45));
} catch (error) {
  console.log('FALLA ->', (error as Error).message);
}
await pool.end();
process.exit(0);
