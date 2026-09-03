import { hash, verify } from '@node-rs/argon2';
import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';
import { and, eq, gt } from 'drizzle-orm';
import { db } from './db';
import { sessions, users, type User } from './db/schema';

/** Parámetros mínimos que recomienda OWASP para Argon2id. */
const ARGON = { memoryCost: 19_456, timeCost: 2, parallelism: 1 } as const;

const SESSION_DAYS = 30;

export function hashPassword(password: string): Promise<string> {
  return hash(password, ARGON);
}

export function checkPassword(password: string, stored: string): Promise<boolean> {
  return verify(stored, password, ARGON).catch(() => false);
}

function sha256(value: string): string {
  return createHash('sha256').update(value).digest('hex');
}

/**
 * El token que ve el launcher es "id.secreto". En la base guardamos el id en claro
 * (para poder buscarlo) y solo el hash del secreto, así una copia de la base no
 * alcanza para entrar como otro.
 */
export async function createSession(userId: number): Promise<string> {
  const id = randomBytes(16).toString('hex');
  const secret = randomBytes(32).toString('base64url');
  const expiresAt = new Date(Date.now() + SESSION_DAYS * 24 * 60 * 60 * 1000);

  await db.insert(sessions).values({ id, userId, secretHash: sha256(secret), expiresAt });
  return `${id}.${secret}`;
}

export async function userFromToken(token: string | null | undefined): Promise<User | null> {
  if (!token) return null;
  const separator = token.indexOf('.');
  if (separator <= 0) return null;

  const id = token.slice(0, separator);
  const secret = token.slice(separator + 1);

  const rows = await db
    .select({ session: sessions, user: users })
    .from(sessions)
    .innerJoin(users, eq(users.id, sessions.userId))
    .where(and(eq(sessions.id, id), gt(sessions.expiresAt, new Date())))
    .limit(1);

  const row = rows[0];
  if (!row) return null;

  const expected = Buffer.from(row.session.secretHash, 'utf8');
  const actual = Buffer.from(sha256(secret), 'utf8');
  if (expected.length !== actual.length || !timingSafeEqual(expected, actual)) return null;

  return row.user;
}

export function bearerToken(request: Request): string | null {
  const header = request.headers.get('authorization');
  if (!header?.startsWith('Bearer ')) return null;
  return header.slice('Bearer '.length).trim() || null;
}

export async function revokeSessions(userId: number): Promise<void> {
  await db.delete(sessions).where(eq(sessions.userId, userId));
}

export async function revokeSession(token: string): Promise<void> {
  const id = token.split('.')[0];
  if (id) await db.delete(sessions).where(eq(sessions.id, id));
}
