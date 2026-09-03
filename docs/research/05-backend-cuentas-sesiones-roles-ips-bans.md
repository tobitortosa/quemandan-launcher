# Backend (cuentas, sesiones, roles, IPs, bans, whitelist, manifest) y hosting de archivos del pack para el launcher privado — comparación Vercel/Next.js vs ASP.NET Core en VPS/PaaS vs Cloudflare Workers, seguridad mínima viable, encuadre legal (Ley 25.326) y panel de admin. Verificado el 2026-09-03.

## Recomendación
RECOMENDACIÓN ÚNICA (plan A): backend TypeScript con Next.js 16 (App Router + Route Handlers) desplegado en Vercel Hobby con región gru1, Postgres en Neon Free (aws-sa-east-1) y Drizzle ORM 0.45 + drizzle-kit; auth propia sin librería de auth: registro username+password con regla `^[A-Za-z0-9_]{3,16}$`, unicidad sobre lower(username), casing canónico inmutable (porque el servidor deriva el UUID offline del nombre exacto), nombres PEPE/Chichon/Titit0N/Luquitas1410 pre-sembrados y reclamables con código; sin email ni CAPTCHA: el alta se hace con código de invitación generado por admin o queda 'pendiente' hasta que el admin autoriza (cubre tu requisito de 'autorizar' y frena spam); hashing Argon2id via @node-rs/argon2 (m=19456, t=2, p=1); sesiones opacas estilo Lucia (id 16 bytes + secret 32 bytes aleatorios, SHA-256 del secret en DB, comparación constante, 30 días sliding, revocación inmediata al banear); rate limit del login por IP con la regla WAF de Vercel (1 regla Hobby) + contador por cuenta en Postgres (bloqueo progresivo tras 5 fallos); tabla audit_log de acciones admin y tabla login_events con IP retenida 60 días (job diario de purga con el cron Hobby, que solo permite 1/día) + aviso de privacidad de un párrafo en el registro (finalidad, retención, contacto, derechos arts. 14-16). Whitelist: al autorizar/banear, el Route Handler llama a la Pterodactyl Client API de Minehost (`POST /api/client/servers/{id}/command` con `whitelist add|remove <nombre>`; key ptlc_ guardada como env var) y además genera el whitelist.json esperado para poder subirlo por FTP como fallback manual; botón 'resync' en el panel. Manifest: endpoint `GET /api/manifest` (o JSON estático versionado en `public/` del mismo deploy) con sha1/tamaño/URL por archivo, ETag y firma Ed25519 opcional; mods y shaderpack apuntan a cdn.modrinth.com; configs (KBs) como assets del mismo deploy o zip versionado en GitHub Releases; instalador del launcher (50–200 MB) en GitHub Releases usando `releases/latest/download/<asset>`. Panel de admin: páginas web dentro del mismo proyecto Next.js protegidas por rol `admin` (usuarios, pendientes, IPs recientes, bans, resync whitelist, códigos de invitación, audit log); el launcher NO incluye panel (mantenerlo 'un botón JUGAR'). Justificación: es el stack que ya operás (Next.js en Vercel), costo US$0, cero servidores que administrar, Argon2id y tokens opacos sin fricción, latencia razonable desde Argentina (gru1 + sa-east-1), y el panel web es usable desde el celular y por otros admins. Descartes verificados: Cloudflare Workers Free (10 ms CPU y PBKDF2 tope 100k → hashing inseguro, D1 sin región Sudamérica, tooling OpenNext frágil en Windows); Supabase (pausa a 7 días); Turso (archivo a 10 días); Render free (sin disco); Fly (sin free tier). PLAN B (si Vercel Hobby no encaja por la cláusula non-commercial, por el cron diario, o si preferís C#): ASP.NET Core 10 Minimal API + EF Core + SQLite (WAL) con Razor Pages para el admin, en un VPS Hetzner CX23 (≈€6/mes con IPv4) o en Oracle Cloud Always Free (A1 arm64, US$0, con riesgo de 'out of capacity' y reclamo por inactividad), detrás de Caddy (TLS automático) como servicio systemd, backup diario de SQLite a Cloudflare R2 (10 GB gratis, egress gratis) con Litestream o rclone; mismas reglas de auth (Argon2id via Konscious/Isopoh, tokens opacos hasheados), rate limiting con AspNetCore RateLimiter, y la misma integración Pterodactyl (aquí sí podés fijar la IP del VPS en la API key). El launcher habla con cualquiera de los dos backends por la misma API REST (`/auth/register`, `/auth/login`, `/auth/logout`, `/me`, `/manifest`, `/admin/*`), así que la decisión es reversible si definís el contrato primero.

## Hallazgos (42)

1. [high] Vercel NO tiene runtime .NET/C#. Runtimes oficiales hoy: Node.js, Bun, Python, Rust, Go, Ruby, Wasm y Edge; community: Bash, Deno, PHP. Sí existe la opción de desplegar imágenes OCI (Vercel Container Registry) como Functions, pero es modelo serverless: filesystem read-only + /tmp de 500 MB, funciones archivadas tras 2 semanas sin uso → SQLite persistente en Vercel es inviable aun con contenedor .NET.
   - fuente: https://vercel.com/docs/functions/runtimes
   - notas: Verificado hoy (doc actualizado 2026-08-12). Para Hobby, frameworks no-Next.js quedan limitados a 12 functions por deployment; Next.js bundlea todo en pocas functions.

2. [high] Vercel Hobby: gratis pero restringido a uso 'non-commercial, personal use only' (fair use). Incluye 4 CPU-hrs de Active CPU, 360 GB-hrs de memoria, 1 M invocaciones/mes, duración máx. de función 300 s, 100 deployments/día, logs de runtime por 1 hora, 200 proyectos. Al exceder un límite, la feature se bloquea hasta pasar 30 días (no cobra). No permite conectar repos de organizaciones Git (solo repos personales).
   - fuente: https://vercel.com/docs/plans/hobby
   - notas: Verificado hoy en docs (tabla Functions en https://vercel.com/docs/functions/usage-and-pricing). Un launcher gratuito para amigos encaja en non-commercial; si aparecen donaciones/rangos pagos deja de encajar.

3. [medium] Vercel Hobby: Fast Data Transfer incluido = 100 GB/mes y Edge Requests = 1 M/mes.
   - fuente: https://community.vercel.com/t/why-vercel-hobby-plan-projects-remain-active-after-exceeding-fast-data-transfer-limits/37748
   - notas: Las páginas oficiales de límites renderizan los números por JS y salieron vacías en el fetch; los 100 GB / 1 M están confirmados por la comunidad oficial de Vercel y sitios de terceros 2026. Pro incluye 1 TB / 10 M (https://vercel.com/docs/pricing/regional-pricing).

4. [high] Vercel Cron Jobs en Hobby: hasta 100 crons por proyecto pero SOLO una ejecución por día y precisión de ±59 min (un `0 1 * * *` corre entre 1:00 y 1:59). Expresiones más frecuentes fallan el deploy. Pro: cada minuto.
   - fuente: https://vercel.com/docs/cron-jobs/usage-and-pricing
   - notas: Impacto: no sirve para 'sincronizar whitelist cada 5 min'; la sync debe ser síncrona al aprobar/banear, con botón manual de resync.

5. [high] Vercel WAF Rate Limiting está disponible en Hobby: 1 regla por proyecto (hasta 3 reglas custom de firewall en total), claves IP o JA4, ventana 10 s–10 min, algoritmo fixed window, 1 M requests permitidos incluidos. Los contadores son por región.
   - fuente: https://vercel.com/docs/vercel-firewall/vercel-waf/rate-limiting
   - notas: Alcanza para limitar /api/auth/login por IP sin infraestructura extra. El límite por cuenta (username) hay que hacerlo en la app (contador en Postgres o Upstash).

6. [high] Vercel Functions corren por defecto en iad1 (Washington) y en Hobby se puede cambiar a una sola región; gru1 (São Paulo) existe y es la más cercana a Buenos Aires.
   - fuente: https://vercel.com/docs/functions/runtimes
   - notas: Verificado hoy. Combinar con Neon en aws-sa-east-1 para que función y DB estén en la misma región.

7. [high] Hetzner Cloud subió precios el 15-jun-2026: CX23 (2 vCPU, 4 GB, 40 GB NVMe, 20 TB tráfico) pasó de €3,99 a €5,49/mes; CAX11 (Arm) €4,49→€5,99; CPX22 €7,99→€19,49 (+144 %). IPv4 primaria: €0,50/mes extra. Precios sin IVA. La página de la línea Cost-Optimized (CX/CAX) mostraba hoy 'currently unavailable' (sin stock).
   - fuente: https://northflank.com/blog/hetzner-cloud-server-price-increases
   - notas: Estructura de planes verificada en https://www.hetzner.com/cloud/cost-optimized/ y /regular-performance/ (precios ocultos por JS); montos vía Northflank, wz-it y costgoat (datos 2026-08-02). CPX12 (1 vCPU/2 GB) aparece como plan EU nuevo; su precio (~€14,27 según terceros) no pude confirmarlo en Hetzner → tratar como low. Costo real de un VPS mínimo: ~€6/mes + posible IVA.

8. [high] Fly.io ya NO tiene free tier: solo un Free Trial de '2 horas de runtime de máquina o 7 días, lo que ocurra primero' y sin tarjeta; después hay que cargar tarjeta y es pay-as-you-go. shared-cpu-1x 256 MB ≈ US$2,02/mes (Amsterdam), volúmenes US$0,15/GB/mes.
   - fuente: https://fly.io/docs/about/free-trial/
   - notas: Precios en https://fly.io/docs/about/pricing/. Los volúmenes sirven para SQLite (con Litestream/LiteFS). Costo estimado real: US$2–3/mes.

9. [high] Railway: plan Free = US$0 con US$1 de crédito de uso mensual; Trial = US$5 una sola vez (30 días, sin tarjeta); Hobby = US$5/mes con US$5 de crédito. Tarifas: ~US$10/GB RAM-mes, ~US$20/vCPU-mes, volúmenes ~US$0,15/GB-mes.
   - fuente: https://railway.com/pricing
   - notas: Con US$1/mes no alcanza para una API ASP.NET Core siempre encendida (~120–200 MB RSS ≈ US$1,2–2 solo en RAM). Con Hobby (US$5) sí, y los volúmenes permiten SQLite.

10. [high] Render Free: web services se apagan tras 15 min sin tráfico (≈1 min de arranque), 750 horas/mes por workspace, y NO admite discos persistentes en free → SQLite se pierde en cada redeploy/spin-down. Postgres free expira a los 30 días (borrado a los 14 días de expirar), 1 GB, sin backups.
   - fuente: https://render.com/docs/free
   - notas: Descartado para SQLite. Solo serviría con DB externa (Neon) y tolerando cold starts de ~1 min en el login.

11. [medium] Azure App Service Linux F1 (Free): cómputo compartido con 60 minutos de CPU/día, 1 GB de storage, sin Always On, sin dominio custom/SSL, 'intended for trials'. Basic B1 ≈ US$13,14/mes (Dev/Test ≈ US$9,49 con suscripción Visual Studio).
   - fuente: https://azure.microsoft.com/en-us/pricing/details/app-service/linux/
   - notas: F1 verificado hoy; el precio B1 sale de terceros (la página oficial renderiza '$-' hasta elegir región). App Service tiene /home persistente, así que SQLite funcionaría en F1, pero con 60 CPU-min/día y sleep.

12. [high] Oracle Cloud Always Free hoy: 2× VM.Standard.E2.1.Micro (1/8 OCPU, 1 GB RAM c/u), Ampere A1 con 1.500 OCPU-horas y 9.000 GB-horas/mes (≈2 OCPU + 12 GB continuos), 200 GB de block storage total, 20 GB object storage, 10 TB egress/mes. Instancias 'idle' (CPU <20 %, red <20 %, RAM <20 % en A1 durante 7 días) pueden ser reclamadas; es común el error 'out of host capacity' para A1.
   - fuente: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
   - notas: Verificado hoy. Es la única opción realmente US$0 para correr ASP.NET Core + SQLite en disco persistente, a costa de operar un Linux (Caddy, systemd, backups) y del riesgo de reclamo por inactividad.

13. [high] Neon Free: 100 proyectos, 0,5 GB de storage por proyecto, 100 CU-horas/proyecto/mes (≈400 h de un compute de 0,25 CU), autoscaling hasta 2 CU, scale-to-zero tras 5 min de inactividad (no desactivable), 10 branches, 5 GB de egress. Región aws-sa-east-1 (São Paulo) disponible.
   - fuente: https://neon.com/pricing
   - notas: Regiones en https://neon.com/docs/introduction/regions. Cold start del compute ~cientos de ms en el primer login tras 5 min idle. Launch: US$0,106/CU-hora + US$0,35/GB-mes.

14. [medium] Neon: 'Projects on the Free plan that have been inactive for 90 days or more are subject to deletion as of October 5, 2026'.
   - fuente: https://neon.com/docs/introduction/regions
   - notas: La frase aparece en la doc de regiones (contexto de deprecación de Azure) y la recoge la búsqueda; la página de planes no la menciona. Para una comunidad activa no es problema; conviene igual un backup semanal (pg_dump) automatizado.

15. [high] Supabase Free: 500 MB de DB (shared CPU, 500 MB RAM), 5 GB egress, 1 GB storage, 50.000 MAU, 2 proyectos activos, 500k invocaciones de Edge Functions, y los proyectos se PAUSAN tras 1 semana de inactividad. Pro desde US$25/mes.
   - fuente: https://supabase.com/pricing
   - notas: La pausa a los 7 días es peor que el scale-to-zero de Neon para una comunidad chica; requiere despausar a mano desde el dashboard.

16. [high] Turso (libSQL) Free: 100 databases, 5 GB, 500 M row reads/mes, 10 M row writes/mes; Developer US$4,99/mes. Las bases del plan free se ARCHIVAN tras 10 días de inactividad y hay que desarchivarlas vía API (POST /v1/organizations/{org}/groups/{group}/unarchive).
   - fuente: https://docs.turso.tech/api-reference/groups/unarchive
   - notas: Límites en https://turso.tech/pricing. Ventaja: SQLite-compatible (mismo esquema si migrás a un VPS con SQLite). Desventaja: el archivado a los 10 días.

17. [high] Cloudflare Workers Free: 100.000 requests/día, 10 ms de CPU por request, 128 MB, script ≤3 MB comprimido, 50 subrequests. Paid: US$5/mes, 10 M requests y 30 M ms CPU incluidos, 30 s de CPU por request (hasta 5 min).
   - fuente: https://developers.cloudflare.com/workers/platform/limits/
   - notas: Precios en https://developers.cloudflare.com/workers/platform/pricing/.

18. [high] En Workers, WebCrypto limita PBKDF2 a 100.000 iteraciones (issue abierto en workerd) — por debajo de OWASP (600k para SHA-256) — y Argon2id con 19 MiB/t=2 no entra en los 10 ms de CPU del plan Free. Hashear contraseñas correctamente en Workers exige el plan Paid (US$5/mes).
   - fuente: https://github.com/cloudflare/workerd/issues/1346
   - notas: Confirmado también por https://lord.technology/2024/02/21/hashing-passwords-on-cloudflare-workers.html (iteraciones típicas 20k–80k en Free). Es el motivo principal para descartar Workers Free como backend de auth.

19. [high] Cloudflare D1 Free: 5 M filas leídas/día, 100.000 filas escritas/día, 5 GB total; Paid: 25 B lecturas y 50 M escrituras/mes incluidas, US$0,75/GB-mes extra. D1 NO tiene ubicación en Sudamérica: 'D1 location hints are not currently supported for South America (sam)... D1 databases do not run in these locations'.
   - fuente: https://developers.cloudflare.com/d1/configuration/data-location/
   - notas: Precios en https://developers.cloudflare.com/d1/platform/pricing/. Desde Argentina, cada query iría a Norteamérica (~120–150 ms estimados).

20. [high] Cloudflare R2: 10 GB-mes de storage, 1 M operaciones Class A y 10 M Class B gratis por mes; egress gratis; luego US$0,015/GB-mes. El subdominio r2.dev público está 'rate-limited and should only be used for development purposes'; para producción hace falta un custom domain administrado en Cloudflare (habilita cache/WAF).
   - fuente: https://developers.cloudflare.com/r2/pricing/
   - notas: Custom domains: https://developers.cloudflare.com/r2/buckets/public-buckets/. Implica tener un dominio propio en Cloudflare (Registrar a costo, ~US$10/año para .com — conocimiento previo, no verificado hoy).

21. [high] Cloudflare Workers Static Assets: 'Requests to static assets are free and unlimited' en todos los planes, pero cada archivo ≤25 MiB y máx. 20.000 archivos (Free). Sirve para manifest/configs, NO para el instalador de 50–200 MB.
   - fuente: https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/
   - notas: Límites en https://developers.cloudflare.com/workers/platform/limits/#static-assets.

22. [medium] Next.js en Cloudflare Workers vía @opennextjs/cloudflare soporta Next 16 y los últimos minors de 15, requiere nodejs_compat, no soporta Node Middleware, y 'Windows support is not guaranteed' (usar WSL). Límite de tamaño 3 MB comprimido en Free / 10 MB en Paid. Cloudflare ahora recomienda su nuevo path 'vinext' para Next.js.
   - fuente: https://opennext.js.org/cloudflare
   - notas: Verificado hoy; el path vinext aparece en https://developers.cloudflare.com/workers/frameworks/framework-guides/nextjs/. Fricción de tooling alta para un dev en Windows comparado con Vercel.

23. [high] GitHub Releases: cada archivo debe ser <2 GiB, hasta 1.000 assets por release, y 'There is no limit on the total size of a release, nor bandwidth usage'. URL estable al último instalador: https://github.com/<owner>/<repo>/releases/latest/download/<asset>.
   - fuente: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
   - notas: Patrón de URL en https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases. Ideal para el instalador (50–200 MB) y opcionalmente para un zip de configs versionado. Evitar la REST API para descubrir releases: 60 req/h por IP sin auth (https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

24. [high] raw.githubusercontent.com devuelve `Cache-Control: max-age=300` (5 minutos) — verificado hoy con curl — y la comunidad reporta rate limiting agresivo por IP (HTTP 429) en *.githubusercontent.com tras el endurecimiento de límites no autenticados de mayo 2025.
   - fuente: https://github.blog/changelog/2025-05-08-updated-rate-limits-for-unauthenticated-requests/
   - notas: Evidencia local: `curl -I https://raw.githubusercontent.com/vercel/next.js/canary/package.json` → 200, Cache-Control: max-age=300. Reportes: https://github.com/orgs/community/discussions/157940. Para ≤100 clientes que consultan 1 vez por arranque es tolerable, pero servir el manifest desde el backend (o Vercel static) es más controlable y permite firmarlo.

25. [medium] Vercel Blob: sin costo en Hobby dentro de límites (al excederlos se bloquea 30 días), storage US$0,023–0,041/GB-mes y transferencia US$0,05–0,117/GB en Pro; blobs >512 MB nunca se cachean (cada acceso es MISS); rate limit Hobby 20 ops simples/s y 15 avanzadas/s; máximo 5 TB por archivo.
   - fuente: https://vercel.com/docs/vercel-blob/usage-and-pricing
   - notas: Los montos incluidos en Hobby (por conocimiento previo: ~1 GB storage, ~10 GB transferencia, 100k simples, 10k avanzadas) no aparecen en el HTML fetchado (placeholders JS) → confidence low para esos números. No lo necesitás: instalador → GitHub Releases, mods/shader → Modrinth, manifest/configs → el propio deploy.

26. [high] OWASP Password Storage: Argon2id con m=19456 (19 MiB), t=2, p=1 como mínimo (equivalentes: 46 MiB/t=1, 12 MiB/t=3, 9 MiB/t=4, 7 MiB/t=5). bcrypt: work factor ≥10 y límite de 72 bytes de input. scrypt: N=2^17, r=8, p=1 (o equivalentes).
   - fuente: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
   - notas: En Vercel Node (memoria por defecto ~1,7 GB) Argon2id 19–46 MiB es trivial; en Workers Free no.

27. [high] Librerías npm verificadas hoy: @node-rs/argon2 2.2.0 (MIT; binarios prebuilt para win32-x64/ia32/arm64, linux-x64 gnu+musl, linux-arm64, darwin, wasm) → funciona en Vercel Node y en Windows; argon2 (node-argon2) 0.45.1; bcrypt 6.0.0; drizzle-orm 0.45.2 (Apache-2.0) + drizzle-kit 0.31.10; @neondatabase/serverless 1.1.0; @libsql/client 0.18.0; hono 4.13.5; better-auth 1.7.2; @upstash/ratelimit 2.0.8; rcon-client 4.2.5; next 16.3.4 (Node ≥20.9).
   - fuente: https://registry.npmjs.org/@node-rs/argon2/latest
   - notas: Consultas directas a registry.npmjs.org. Prisma: el dist-tag `latest` apunta a 8.0.0-rc.12 (publicado 2026-08-26) y exige Node ≥22.18; la última estable es 7.10.0 (2026-08-25). Si usás Prisma, pinneá 7.x; Drizzle es más liviano para serverless y sin engine binario.

28. [high] Auth.js (next-auth) desalienta el Credentials provider: 'By default, the Credentials provider does not persist data in the database', solo sesiones JWT (no database sessions), y el dev debe implementar hashing, rate limiting y reset por su cuenta. No aporta valor para un launcher username+password.
   - fuente: https://authjs.dev/getting-started/authentication/credentials
   - notas: Verificado hoy.

29. [high] Better Auth 1.7.2: el plugin `username` (3–30 chars por defecto, alfanumérico + `_` + `.`, normaliza a minúsculas y guarda displayUsername, validadores custom) SIGUE exigiendo email en el sign-up; existe plugin `bearer` (token via header set-auth-token) con advertencia de uso cauteloso; sesiones 7 días por defecto, updateAge 1 día, revokeSession/revokeOtherSessions/revokeSessions.
   - fuente: https://www.better-auth.com/docs/plugins/username
   - notas: Bearer: https://www.better-auth.com/docs/plugins/bearer; sesiones: https://www.better-auth.com/docs/concepts/session-management. Para 'registro sin email' habría que inventar emails placeholder → más simple implementar auth propia (≈200 líneas).

30. [high] Lucia fue deprecada en marzo 2025 y hoy es material de referencia. Su implementación de referencia (auth_session.ts) usa: id aleatorio de 80 bits + secret de 32 bytes aleatorios enviados como `id.secretBase64`; en DB se guarda solo SHA-256(secret); comparación en tiempo constante; expiración de 10 días con refresco de `tokenLastVerifiedAt` como máximo cada hora.
   - fuente: https://raw.githubusercontent.com/lucia-auth/lucia/refs/heads/main/code/auth_session.ts
   - notas: Patrón recomendado para tokens opacos del launcher (mejor que JWT: revocación inmediata al banear con un DELETE). Adaptar a 30 días sliding para no pedir login seguido.

31. [high] Cloudflare Turnstile es gratis (20 widgets, 10 hostnames por widget) pero es un challenge JS embebido en una página web: en un launcher de escritorio requiere webview; para este caso conviene reemplazar CAPTCHA por códigos de invitación / aprobación de admin.
   - fuente: https://developers.cloudflare.com/turnstile/plans/
   - notas: Verificado hoy.

32. [high] Upstash Redis Free: 500.000 comandos/mes, 256 MB, 10 GB de ancho de banda, 1 database, sin tarjeta; PAYG US$0,2 por 100k comandos. Útil como store para rate limiting por cuenta en serverless, aunque un contador en Postgres alcanza para ≤100 usuarios.
   - fuente: https://upstash.com/pricing/redis
   - notas: Verificado hoy.

33. [high] Almacenamiento del token en el launcher: Electron `safeStorage` usa DPAPI en Windows ('only a user with the same logon credential... can decrypt' — protege de otros usuarios, no de otras apps del mismo usuario); en .NET, `System.Security.Cryptography.ProtectedData` (NuGet homónimo) envuelve DPAPI con DataProtectionScope.CurrentUser y es Windows-only (PlatformNotSupportedException fuera de Windows).
   - fuente: https://www.electronjs.org/docs/latest/api/safe-storage
   - notas: .NET: https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.protecteddata. Preferir las APIs async de safeStorage (las sync podrían deprecarse).

34. [high] Usernames de Minecraft Java: 3–16 caracteres, solo A–Z, a–z, 0–9 y `_` (63 caracteres posibles) y únicos sin distinguir mayúsculas (case-insensitive). Regla para el launcher: `^[A-Za-z0-9_]{3,16}$` + índice único sobre lower(username) + reservar PEPE, Chichon, Titit0N, Luquitas1410 y el quinto jugador.
   - fuente: https://mcprofiles.me/guides/minecraft-username-rules
   - notas: Longitud verificada en https://minecraft.wiki/w/Player#Username ('3-16 characters', '63 characters to choose from'); set de caracteres y unicidad case-insensitive por fuentes secundarias consistentes.

35. [high] En online-mode=false el servidor IGNORA el UUID que manda el cliente y deriva uno estable del nombre exacto: UUID v3 = MD5('OfflinePlayer:' + nombre) — con mayúsculas/minúsculas incluidas — y ese UUID es el que va a whitelist.json, ops.json y playerdata. Comprobado por cálculo: el UUID de TLauncher para PEPE (5b071e1f-3a11-4f28-… es v4 aleatorio) NO coincide con el offline UUID 7a067f19-b48d-3c6e-9039-8f37f64def1f; 'pepe' daría 9ec9a777-…. Conclusión: el launcher nuevo conserva inventario/whitelist si envía exactamente 'PEPE', y el username debe guardarse con casing canónico inmutable.
   - fuente: https://sr.ht/~kota/mcoffline/
   - notas: Algoritmo y comportamiento del servidor confirmados por fuentes secundarias (mcoffline, mclist.io offline UUID generator); cálculo local reproducido en Python. Consecuencia de seguridad: en offline-mode la whitelist por nombre NO autentica — cualquiera que conozca un nombre whitelisteado puede entrar con otro launcher; la autenticación real la da solo el servidor (mod/plugin de login o allowlist por IP).

36. [high] server.properties (26.x): enable-rcon default false; RCON viaja sin cifrar ('not recommended to connect to rcon via untrusted networks, like the internet... including the rcon password can be intercepted'); rcon.port default 25575; white-list default false pero cambia a true en 26.3; enforce-whitelist expulsa a los no listados al recargar; online-mode=false permite 'hackers with fake accounts'.
   - fuente: https://minecraft.wiki/w/Server.properties
   - notas: Comandos: `whitelist add|remove|list|on|off|reload` (https://minecraft.wiki/w/Commands/whitelist); los OPs entran aunque no estén en la whitelist.

37. [high] Minehost es un hosting argentino (minehost.pro redirige a https://web.minehost.com.ar/buy/, WHMCS) que usa panel Pterodactyl ('Panel Pterodactyl' en todos los planes), con FTP desde el panel ('Archivos > Acceso Archivos FTP', también FileZilla/WinSCP), IP numérica + subdominio gratis, DDoS, datacenter en Argentina. El server del usuario resuelve por SRV `_minecraft._tcp.quemandan.minehost.pro → sv36.minehost.pro:25445`, IP 45.235.98.223 (AS266777 INETGAMING, Buenos Aires).
   - fuente: https://web.minehost.com.ar/buy/index.php?rp=/store/minecraft-en-sa-sur-america
   - notas: SRV/IP verificados hoy con Resolve-DnsName e ipinfo.io. Ojo: el puerto real es 25445 vía SRV, no 25565; el launcher solo debe pasar el hostname y dejar que el cliente resuelva el SRV. Guías de Minehost: mods vía FTP (KB/27), whitelist con comandos (KB/37), seguridad no-premium con plugins Paper (KB/45 — no aplica a Fabric). panel.minehost.pro respondió Cloudflare 530 hoy → URL del panel desconocida.

38. [medium] Pterodactyl Client API permite ejecutar comandos de consola por HTTPS sin RCON: `POST /api/client/servers/{server_id}/command` con body `{"command":"whitelist add PEPE"}`, headers `Authorization: Bearer ptlc_…`, `Accept: Application/vnd.pterodactyl.v1+json`, `Content-Type: application/json`; `GET /api/client` lista servers; la key se crea en `https://<panel>/account/api` (opcionalmente restringida por IPs); rate limit 240 req/min; devuelve 412 si el server está apagado.
   - fuente: https://pteroapi.com/docs/api/client
   - notas: API estándar de Pterodactyl 1.x verificada en docs comunitarias; NO pude verificar que Minehost tenga habilitada la sección Account → API Credentials para clientes (depende del host). Las funciones de Vercel no tienen IP fija (Static IPs es add-on Pro US$100/mes), así que la restricción por IP de la key no aplicaría.

39. [high] Ley 25.326 (vigente, sin reemplazo): art. 2 define dato personal ('información de cualquier tipo referida a personas físicas o de existencia ideal'); art. 4 exige datos 'ciertos, adecuados, pertinentes y no excesivos' y su destrucción 'cuando hayan dejado de ser necesarios'; art. 5 consentimiento 'libre, expreso e informado'; art. 6 informar previamente finalidad, destinatarios y derechos de acceso/rectificación/supresión; art. 9 medidas de seguridad; art. 10 confidencialidad; arts. 14–16 acceso en 10 días corridos y rectificación en 5 días hábiles; arts. 21 y 24: los particulares que formen archivos 'que no sean para un uso exclusivamente personal' deben inscribirlos en el Registro Nacional de Bases de Datos.
   - fuente: https://servicios.infoleg.gob.ar/infolegInternet/anexos/60000-64999/64790/texact.htm
   - notas: Verificado hoy en InfoLEG. La inscripción se hace por TAD según Res. AAIP 132/2018 (https://www.boletinoficial.gob.ar/detalleAviso/primera/194265/20181022); no pude confirmar hoy si el trámite es gratuito (páginas de argentina.gob.ar devolvieron 403) → low. Una base de ~100 amigos con IPs técnicamente excede el 'uso exclusivamente personal'; el riesgo práctico de fiscalización es bajo pero el plan debería mencionarlo.

40. [high] Res. AAIP 47/2018 aprueba 'Medidas de Seguridad Recomendadas' (referenciales, no obligatorias) para tratamiento informatizado: control de acceso y autenticación, segregación de roles, control de cambios, backups y recuperación, gestión de vulnerabilidades, destrucción segura, gestión de incidentes y entornos de desarrollo seguros.
   - fuente: https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-47-2018-312662/texto
   - notas: Verificado hoy. Un backend con Argon2id, roles, audit log, backups y retención acotada de IPs cumple el espíritu de esta guía.

41. [medium] Reforma de la Ley 25.326: hay proyectos en el Congreso (p. ej. 1751-D-2026) inspirados en el anteproyecto de la AAIP, que perdió estado parlamentario a fines de 2024; incorporan accountability, privacy by design, portabilidad. Ninguno está sancionado: rige la 25.326.
   - fuente: https://iapp.org/news/a/se-impulsa-un-nuevo-proyecto-de-reforma-del-r-gimen-de-protecci-n-de-datos-en-argentina
   - notas: Estado según búsqueda de hoy. No encontré hoy un dictamen AAIP explícito sobre direcciones IP como dato personal; tratarlas como dato personal por precaución (criterio GDPR/UE) y retenerlas 30–90 días.

42. [medium] Costo mensual estimado de la opción TypeScript: Vercel Hobby US$0 + Neon Free US$0 + GitHub Releases US$0 + Modrinth CDN US$0 = US$0 (dominio propio opcional ≈US$10/año). Opción C#: Hetzner CX23 ≈€6/mes (+IVA si aplica) u Oracle Always Free US$0 con riesgo de capacidad/reclamo; Railway Hobby US$5; Fly ≈US$2–3.
   - fuente: https://neon.com/pricing
   - notas: Síntesis de los hallazgos anteriores; el IVA de Hetzner depende del país de facturación.

## Riesgos
- Vercel Hobby es solo para uso no comercial: si la comunidad cobra rangos, acepta donaciones o crece a un server público con ingresos, hay que migrar a Pro (US$20/seat) o al plan B (VPS).
- La integración con la whitelist depende de que Minehost exponga en su Pterodactyl la sección Account → API Credentials (no verificado hoy; panel.minehost.pro devolvió 530). Fallbacks: RCON (sin cifrar y quizá sin puerto asignado) o subida manual de whitelist.json por FTP.
- En online-mode=false la whitelist por nombre no autentica: cualquiera que conozca un nombre autorizado entra con otro launcher. El launcher + backend controlan quién recibe el pack, pero la seguridad real del server exige un mod/plugin de login server-side (p. ej. un mod Fabric de auth que valide contra tu backend) o allowlist de IPs — alcance adicional que el plan debe decidir.
- Cambiar el casing de un username (PEPE → Pepe) genera otro UUID offline y 'pierde' inventario/whitelist en el server: el username debe ser inmutable y el launcher debe enviarlo exactamente.
- Cold starts: Neon suspende el compute a los 5 min y Vercel archiva funciones de producción sin uso tras 2 semanas → el primer login puede tardar 1–3 s; aceptable pero hay que mostrar spinner y no reintentar agresivamente.
- Neon Free: proyectos inactivos ≥90 días son candidatos a borrado desde el 2026-10-05; sin backups fuera de Neon se puede perder la base. Mitigación: pg_dump semanal automatizado (GitHub Actions) a un repo privado o R2.
- Cron de Vercel Hobby solo una vez por día y con ±59 min de imprecisión: cualquier tarea periódica (purga de IPs, resync) debe tolerar eso; nada crítico puede depender del cron.
- Sin email no hay recuperación de contraseña self-service: el reset lo hace el admin (código de un solo uso) — hay que asumir la carga operativa o pedir un dato de contacto opcional (Discord).
- Las funciones de Vercel no tienen IP fija: no podés restringir la API key de Pterodactyl por IP ni pedirle a Minehost que allowlistee tu backend; si comprometen la key, rotarla desde el panel.
- raw.githubusercontent.com tiene rate limiting por IP y cache de 5 min: no usarlo como CDN del manifest si el launcher hace polling; servirlo desde el backend/deploy con ETag.
- Ley 25.326: una base con ~100 personas e IPs excede 'uso exclusivamente personal' y formalmente debería inscribirse en el RNBD (TAD); riesgo práctico bajo, pero el plan debería incluir aviso de privacidad, retención acotada de IPs (30–90 días) y borrado de cuentas a pedido.
- Hetzner subió precios +33–176 % en junio 2026 y la línea CX mostraba 'currently unavailable' hoy; Oracle Always Free sufre 'out of host capacity' y reclama instancias idle a los 7 días: el plan B tiene incertidumbre de disponibilidad.
- Prisma `latest` es un release candidate (8.0.0-rc.12) que exige Node ≥22.18: si se elige Prisma hay que pinnear 7.10.x; Drizzle evita el problema.
- Cloudflare R2 sin dominio propio en Cloudflare solo ofrece r2.dev (rate-limited, 'development purposes'): no usar R2 salvo que ya tengas dominio en Cloudflare.
- A partir de Minecraft 26.3 white-list pasa a default true: si Minehost reinstala el server o migra versión, el server puede quedar cerrado hasta que el backend/whitelist se resincronice.

## Preguntas para el usuario
- ¿Tu panel de Minehost (Pterodactyl) tiene la sección 'Cuenta → Credenciales de API' (URL tipo https://<panel>/account/api) y cuál es la URL del panel? Si no la tiene, ¿Minehost te habilita RCON con puerto propio? Esto decide si la whitelist se sincroniza automáticamente o queda manual.
- ¿La comunidad va a manejar dinero alguna vez (donaciones, rangos, aportes al hosting)? Determina si Vercel Hobby (uso no comercial) es admisible o hay que ir directo a VPS/Pro.
- ¿Aceptás que el registro sea 'solo con código de invitación' o 'pendiente hasta que un admin apruebe' en lugar de abierto con email/CAPTCHA? Cambia el flujo del launcher y del panel.
- ¿Querés administrar desde el celular u otros admins además de vos? Si sí, el panel web (Next.js) es obligatorio; si solo vos desde tu PC, podría vivir en el launcher.
- ¿Tenés un dominio propio (y cuenta de Cloudflare)? Define si la API va en <tu-dominio> o en *.vercel.app y si R2 es una opción.
- ¿Querés que el server exija autenticación real (mod Fabric server-side que valide contra tu backend) o te alcanza con whitelist por nombre sabiendo que en offline-mode cualquiera con el nombre puede entrar?
- Sin email: ¿te parece bien que el reset de contraseña lo haga el admin a mano (código de un solo uso por Discord), o preferís pedir un contacto opcional (Discord ID/email) en el registro?
