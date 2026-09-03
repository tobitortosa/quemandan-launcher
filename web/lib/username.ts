/**
 * Reglas del nombre de jugador. Son las de Minecraft, no una elección nuestra:
 * de 3 a 16 caracteres, letras, números y guion bajo.
 *
 * El nombre es inmutable a propósito. El servidor corre en modo offline, así que
 * calcula el UUID del jugador a partir del nombre exacto, mayúsculas incluidas.
 * Cambiarlo equivale a perder el inventario y el progreso.
 */
const PATTERN = /^[A-Za-z0-9_]{3,16}$/;

export function isValidUsername(value: string): boolean {
  return PATTERN.test(value);
}

export function normalize(value: string): string {
  return value.toLowerCase();
}

export const USERNAME_RULE =
  'El nombre tiene entre 3 y 16 caracteres y solo puede tener letras, números y guion bajo.';
