import Image from 'next/image';
import { env } from '@/lib/env';
import { socials } from './socials';

// El link de descarga viene de una variable de entorno: se lee en cada pedido, así
// cambiarlo no obliga a recompilar el sitio.
export const dynamic = 'force-dynamic';

export const metadata = {
  title: 'SOBRINOS DE PEPE · Launcher',
  description: 'Descargá el launcher del servidor y entrá a jugar.',
};

/** Flecha que avisa que el enlace abre en otra pestaña. */
function ExternalArrow() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function Home() {
  const download = env.downloadUrl;

  return (
    <main className="page">
      <div className="card">
        <Image src="/logo.png" alt="Sobrinos de Pepe" width={128} height={128} priority className="logo" />

        <h1>SOBRINOS DE PEPE</h1>
        <p className="lead">
          Descargá el launcher, creá tu cuenta y esperá que te aprueben. Después es apretar
          JUGAR: el Minecraft, el Java y los mods se instalan solos.
        </p>

        {download ? (
          <a className="download" href={download}>
            Descargar para Windows
          </a>
        ) : (
          <p className="pending">La descarga todavía no está publicada.</p>
        )}

        <p className="requisitos">
          Windows de 64 bits · 2 GB libres · no toca tu Minecraft actual
        </p>

        <div className="redes">
          {socials.map((social) => (
            <a
              key={social.name}
              href={social.url}
              target="_blank"
              rel="noopener noreferrer"
              className="red"
              style={{ ['--tono' as string]: social.color }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d={social.path} />
              </svg>
              <span className="nombre">{social.name}</span>
              <span className="arroba">@{social.handle}</span>
              <ExternalArrow />
            </a>
          ))}
        </div>
      </div>
    </main>
  );
}
