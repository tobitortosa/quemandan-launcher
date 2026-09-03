function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Falta la variable de entorno ${name}.`);
  return value;
}

export const env = {
  get databaseUrl() {
    return required('DATABASE_URL');
  },
  /** Clave de la API de Pterodactyl (ptlc_...). Vive solo acá, nunca en el launcher. */
  get pterodactylKey() {
    return required('PTERODACTYL_KEY');
  },
  get pterodactylUrl() {
    return process.env.PTERODACTYL_URL ?? 'https://pterodactyl.minehost.com.ar';
  },
  get pterodactylServerId() {
    return process.env.PTERODACTYL_SERVER_ID ?? 'dbd3f1e9';
  },
  get minecraftVersion() {
    return process.env.MINECRAFT_VERSION ?? '26.1';
  },
  get fabricLoader() {
    return process.env.FABRIC_LOADER ?? '0.19.5';
  },
  get serverName() {
    return process.env.SERVER_NAME ?? 'SOBRINOS DE PEPE';
  },
  get serverAddress() {
    return process.env.SERVER_ADDRESS ?? 'sobrinosdepepe.minehost.pro';
  },
  get downloadUrl() {
    return process.env.DOWNLOAD_URL ?? '';
  },
};

export const MODRINTH_USER_AGENT =
  process.env.MODRINTH_USER_AGENT ?? 'SobrinosDePepeLauncher/0.1 (tobias.tortosa@soution.com)';
