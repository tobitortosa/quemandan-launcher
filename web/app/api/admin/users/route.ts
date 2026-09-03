import { desc, ilike, or, sql } from 'drizzle-orm';
import { ok, requireAdmin } from '@/lib/api';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

/** La lista de cuentas, con las pendientes primero: es la bandeja de entrada del admin. */
export async function GET(request: Request) {
  const guard = await requireAdmin(request);
  if ('response' in guard) return guard.response;

  const query = new URL(request.url).searchParams.get('q')?.trim();

  const rows = await db
    .select({
      id: users.id,
      username: users.username,
      status: users.status,
      role: users.role,
      createdAt: users.createdAt,
      approvedAt: users.approvedAt,
      bannedAt: users.bannedAt,
    })
    .from(users)
    .where(query ? or(ilike(users.username, `%${query}%`)) : undefined)
    .orderBy(sql`case ${users.status} when 'pending' then 0 when 'active' then 1 else 2 end`, desc(users.createdAt))
    .limit(300);

  return ok({ users: rows });
}
