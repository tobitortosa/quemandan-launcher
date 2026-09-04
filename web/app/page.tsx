import Image from 'next/image';
import { env } from '@/lib/env';
import { socials } from './socials';

// El link de descarga viene de una variable de entorno: se lee en cada pedido, así
// cambiarlo no obliga a recompilar el sitio.
export const dynamic = 'force-dynamic';

/** El código del launcher es público: cualquiera puede leerlo antes de instalarlo. */
const REPO = 'https://github.com/tobitortosa/sobrinosdepepe-launcher';

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

/** Escudo con tilde: el apartado que explica por qué el archivo se puede instalar tranquilo. */
function ShieldIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 2.5 4.5 5.2V11c0 4.6 3.2 8.7 7.5 10.1 4.3-1.4 7.5-5.5 7.5-10.1V5.2L12 2.5Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path
        d="m8.8 11.9 2.2 2.2 4.2-4.4"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 .5a11.5 11.5 0 0 0-3.6 22.4c.6.1.8-.2.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.4-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.1.1 1.7 1.2 1.7 1.2 1 1.8 2.7 1.3 3.4 1 .1-.7.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.2 1.2a11 11 0 0 1 5.8 0c2.2-1.5 3.2-1.2 3.2-1.2.6 1.6.2 2.8.1 3.1.8.8 1.2 1.8 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .4.2.7.8.6A11.5 11.5 0 0 0 12 .5Z" />
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

        <section className="seguridad">
          <h2>
            <ShieldIcon />
            Se puede instalar tranquilo
          </h2>

          <ul>
            <li>
              <strong>El código está a la vista.</strong> Todo lo que hace el launcher se puede
              leer antes de instalarlo, línea por línea.
            </li>
            <li>
              <strong>Windows te va a mostrar un aviso.</strong> Va a decir que no conoce el
              programa: es porque el certificado para firmarlo cuesta unos 200 dólares por año
              y no lo vamos a pagar para un servidor de amigos. Tocá <em>Más información</em> y
              después <em>Ejecutar de todas formas</em>.
            </li>
            <li>
              <strong>No toca nada tuyo.</strong> Se instala en tu carpeta de usuario, sin pedir
              permisos de administrador, y tu Minecraft de siempre queda como está.
            </li>
          </ul>

          <a href={REPO} target="_blank" rel="noopener noreferrer" className="repo">
            <GitHubIcon />
            Ver el código en GitHub
            <ExternalArrow />
          </a>
        </section>

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
