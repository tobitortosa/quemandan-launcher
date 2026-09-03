import { env } from '@/lib/env';

export const metadata = {
  title: 'QUE MANDAN · Launcher',
  description: 'Descargá el launcher del servidor y entrá a jugar.',
};

export default function Home() {
  const download = env.downloadUrl;

  return (
    <main
      style={{
        minHeight: '100dvh',
        display: 'grid',
        placeItems: 'center',
        background: '#0f1115',
        color: '#e8e8ea',
        fontFamily: 'system-ui, sans-serif',
        padding: '2rem',
      }}
    >
      <div style={{ maxWidth: '34rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '2.5rem', margin: '0 0 .5rem', letterSpacing: '-.02em' }}>QUE MANDAN</h1>
        <p style={{ color: '#9aa0aa', margin: '0 0 2rem' }}>
          Descargá el launcher, creá tu cuenta y esperá que te aprueben. El resto lo hace solo.
        </p>

        {download ? (
          <a
            href={download}
            style={{
              display: 'inline-block',
              padding: '.9rem 2.5rem',
              borderRadius: '.6rem',
              background: '#4ade80',
              color: '#0f1115',
              fontWeight: 600,
              fontSize: '1.05rem',
              textDecoration: 'none',
            }}
          >
            Descargar para Windows
          </a>
        ) : (
          <p style={{ color: '#f5a524' }}>La descarga todavía no está publicada.</p>
        )}

        <div
          style={{
            marginTop: '2.5rem',
            padding: '1rem 1.25rem',
            border: '1px solid #262a33',
            borderRadius: '.6rem',
            textAlign: 'left',
            color: '#9aa0aa',
            fontSize: '.9rem',
            lineHeight: 1.6,
          }}
        >
          <strong style={{ color: '#e8e8ea' }}>Windows va a mostrar un aviso.</strong> La primera vez
          aparece “Windows protegió tu PC”. Apretá <em>Más información</em> y después{' '}
          <em>Ejecutar de todas formas</em>. Pasa porque el instalador todavía no está firmado; de la
          segunda vez en adelante no vuelve a aparecer.
        </div>

        <p style={{ marginTop: '2rem', color: '#5c626d', fontSize: '.8rem' }}>
          Necesitás Windows de 64 bits y unos 2 GB libres. El launcher instala su propio Java y no
          toca tu Minecraft actual.
        </p>
      </div>
    </main>
  );
}
