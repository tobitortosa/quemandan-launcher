import { drizzle, type NodePgDatabase } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import { env } from '../env';
import * as schema from './schema';

type Database = NodePgDatabase<typeof schema>;

// La conexión se abre en la primera consulta, no al importar el módulo: si no, el build
// de Next fallaría al leer las rutas sin tener DATABASE_URL a mano.
// En serverless cada instancia reusa su pool mientras sigue caliente.
const globalForDb = globalThis as unknown as { pool?: Pool; db?: Database };

function client(): Database {
  if (!globalForDb.db) {
    globalForDb.pool ??= new Pool({
      connectionString: env.databaseUrl,
      // Verificar el certificado del servidor. Con solo "sslmode=require" en la URL,
      // node-postgres cifra pero no valida contra quién habla, y avisa por consola.
      ssl: env.databaseUrl.includes('sslmode=disable') ? false : { rejectUnauthorized: true },
      // Una conexión por instancia: es lo que conviene en serverless y lo que
      // acepta la base de desarrollo.
      max: 1,
      idleTimeoutMillis: 10_000,
    });
    globalForDb.db = drizzle(globalForDb.pool, { schema });
  }
  return globalForDb.db;
}

export const db = new Proxy({} as Database, {
  get: (_target, property) => client()[property as keyof Database],
});

export { schema };
