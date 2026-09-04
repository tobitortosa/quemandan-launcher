# Prompt para rehacer la economía al estilo DonutSMP

Copiar todo lo que sigue en un chat nuevo.

---

Quiero que la economía de mi servidor de Minecraft funcione igual que la de
**DonutSMP**, que es lo que hace divertido a ese servidor: para tener lo mejor
hay que matar gente o jugar muchas horas, nunca farmear tranquilo y comprarlo.

## El servidor

**Fabric 26.1** (Fabric Loader 0.19.5) en Minehost, administrado por Pterodactyl.
No es Paper: **ningún plugin de Bukkit/Spigot sirve**, aunque sea lo primero que
sugiera cualquier guía de SMP. Para buscar mods, la API de Modrinth filtrando por
lo que importa:

```
https://api.modrinth.com/v2/search?query=<qué>&facets=[["categories:fabric"],["versions:26.1"],["server_side:required"]]
```

Un mod con `client_side: unsupported` se instala solo en el servidor y **no hace
falta tocar el launcher ni publicar una versión nueva** para que los jugadores lo
tengan.

## Cómo se toca el servidor

En el repositorio (`C:\Users\Tobi\Desktop\servermc`) está todo listo:

- `servidor/mc.py` — manda comandos y escribe archivos por la API de Pterodactyl.
  `mc.cmd("...")`, `mc.write(ruta, texto)`, `mc.read(ruta)`. **Las credenciales
  salen solas de `web/.env.local`**, no hay que pedirlas ni escribirlas en
  ningún lado.
- `servidor/respaldar.py` — baja del servidor todo lo que mantenemos nosotros.
  **Correlo y commiteá después de cada cambio**: si no, el trabajo vive solo
  dentro del servidor y se pierde.
- `servidor/generar-menu.py` — arma el menú de `/comandos`.
- `servidor/generar-cartel.py` — arma el cartel de la derecha.
- `servidor/configurar-scoreboard.py` — rehace los objetivos y los lugares del
  scoreboard, que el juego guarda dentro del mundo.
- `servidor/LEEME.md` — **leelo primero**, tiene las trampas que ya nos costaron
  horas.

Para leer el log: `mc.read("/logs/latest.log")`. Reiniciar:
`mc.call("/power", {"signal": "restart"})`, avisando antes por chat con
`mc.cmd("say ...")` porque suele haber gente jugando.

## Lo que ya está hecho

**EconomyCraft 1.9.0** (+ Architectury 20.0.12) da la economía: `/bal`,
`/bal top`, `/pay`, `/sell`, `/shop`, `/worth`, `/ah` (subastas entre
jugadores), `/orders` (órdenes de compra), `/daily`, `/transactions`. Su
configuración está en `/config/economycraft/` (`config.json` y `prices.json`
con 1.695 items).

Estado actual de los números:

| Ajuste | Valor |
|---|---|
| Saldo inicial | $1.000 |
| Regalo diario | $100 |
| Impuesto | 10% |
| Límite de venta diario | $10.000 |
| Plata que se lleva quien te mata | 10% |
| Precios dinámicos | apagados (piden 30 días de historial) |

Precios de referencia hoy: diamante $84 (compra $280), netherite ingot $252
(compra $840), elytra $1.050, totem $150. El ratio venta/compra es 31% de
mediana y **no hay ningún item que se compre más barato de lo que se vende**
(eso sería plata infinita; hay que verificarlo después de cada cambio).

**Recompensas** (`/bounty`): un comando de Melius más un datapack en
`/world/datapacks/sobrinosdepepe/` que detecta cuando un jugador mata a otro y
le paga la recompensa que tenía en la cabeza. **Ese datapack ya tiene resuelta
la detección de asesinatos**, que es la pieza que hace falta para los shards:
el advancement marca al asesino y la función de tick lo cruza con quién murió al
final del tick, porque los dos eventos caen en el mismo tick sin orden
garantizado.

**Visión nocturna** (`/nv`), menú de comandos clickeable (`/comandos` con
categorías), cartel a la derecha con dinero, kills, muertes y el precio de tu
cabeza.

## Lo que quiero

### 1. Los números de Donut, escalados con cuidado

Quiero la misma **estructura de precios relativos** que Donut. Ojo con esto,
que es la trampa: los precios que se ven publicados de Donut (netherite ingot
~3,5 millones, elytra 250-320 millones) son del **mercado entre jugadores**
después de años de inflación, **no lo que paga el `/sell` del servidor**. Su
propia guía dice que el `/sell` es "la opción menos rentable" y está ahí para
liquidez rápida.

Entonces:

- Averiguá cuánto paga realmente el `/sell` de Donut por los items comunes, no
  los precios del AH.
- Si vas a subir los precios, **escalá toda la economía junta**: saldo inicial,
  regalo diario, piedra, comida, hierro, todo. Si solo subís el netherite a
  millones y el saldo inicial queda en $1.000, no cambia nada; y si subís los
  precios de venta sin subir los de compra, con dos kills se compra todo.
- Lo que me importa que se cumpla es la **relación**: en Donut una elytra vale
  ~85 veces un ingot de netherite. En mi servidor hoy vale 4 veces. Los items de
  fin del juego están regalados.

### 2. Los shards, igual que allá

Donut tiene **dos monedas que no se pueden intercambiar**:

| | Money | Shards |
|---|---|---|
| Cómo se gana | farmear, vender, comerciar | **10 por matar a un jugador**, 1 cada 10 minutos |
| Para qué sirve | comerciar con otros (`/ah`, `/orders`) | spawners (1.500), llaves de cofres, armas y armaduras |
| Se compra con la otra | no | no |

Ahí está el corazón del diseño: **la moneda que compra las cosas buenas se gana
matando gente**. Un spawner sale 1.500 shards, o sea 150 kills, contra 250 horas
esperando. Matar es 150 veces más rápido que farmear pasivamente.

EconomyCraft tiene una sola moneda, así que los shards hay que construirlos.
Diseño sugerido (ajustalo si encontrás algo mejor):

- Un objetivo de scoreboard `Shards`.
- **+10 al matar a un jugador**, enganchado en el datapack que ya detecta las
  muertes.
- **+1 cada 10 minutos de juego**, con un contador de ticks en la función de
  tick (ojo: que no cuente a los que están AFK con `/afk`, o va a haber gente
  durmiendo con el juego abierto).
- `/shards` para ver el saldo, y una tienda de shards con el menú clickeable de
  Melius Commands: cada compra verifica el score, resta y hace `give`.
- Que se vea en el cartel de la derecha, al lado del dinero.

### 3. Que la tienda no venda lo que hace fuerte

En Donut **no hay tienda del servidor que venda equipamiento por plata**. Hoy en
mi `/shop` se puede comprar netherite ($840 el ingot), armadura completa, espada
($2.841), totems ($500) y nether stars ($3.000). Mientras eso se pueda comprar
con plata farmeada, nadie necesita pelear. Quiero que el equipamiento salga de
jugar, de comerciar con otros o de matar a alguien que ya lo tiene.

## Trampas que ya nos costaron horas

- **Melius Commands: `op_level` no tiene valor por defecto.** Cada ejecución
  necesita `{"silent": true, "as_console": false, "op_level": 4}`. Sin eso el
  comando corre con el nivel del jugador, `tellraw` pide nivel 2, y **al que no
  es operador no le pasa nada al apretar enter, sin ningún error visible**. A un
  operador le funciona todo, así que **probá siempre sin ser operador**:
  `deop <jugador>`, probar, `op <jugador>`.
- **No usar predicados de tipo `permission`** en comandos ni modificadores: la
  `predicate-api 0.8.1` que traen Melius y Styled Sidebars choca con la API de
  permisos de la Fabric API 0.155.2 y **rompe el envío del árbol de comandos**,
  dejando sin comandos a todos los que no sean operadores. Usar
  `{"type": "operator", "operator": 4}`.
- **Al escribir archivos, generá el JSON con `json.dumps` y los símbolos con
  `chr()`.** Una barra invertida suelta dentro de un heredoc termina siendo un
  salto de línea real adentro del comando y lo parte al medio. Ya rompió un
  `tellraw` y una función del datapack.
- **`pack.mcmeta` de un datapack en 26.1 necesita los cuatro campos de versión**
  (`pack_format`, `supported_formats`, `min_format`, `max_format`) y **tienen
  que coincidir entre sí**; el formato del juego es 81.
- **Las etiquetas de versión de Modrinth son más conservadoras que los mods.**
  Antes de subir un `.jar`, leé su `fabric.mod.json` con `zipfile` y mirá
  `depends` de verdad: filtrar por `versions:26.1` nos dio una versión vieja de
  Architectury que **dejó el servidor caído**.
- **`/reload` recarga los datapacks y los comandos de Melius, pero NO el cartel**
  (Styled Sidebars usa `/styledsidebars reload`) ni la configuración de
  EconomyCraft (esa pide reinicio).
- **Cambios de sintaxis de 26.1**: en `tellraw` los eventos son `click_event` /
  `hover_event` con `command` / `value`, y el slot del scoreboard es
  `below_name`, no `belowName`.
- **Para que una función haga de interruptor**, cortala con `return run`: si no,
  apagar algo deja la marca en cero y la línea siguiente lo vuelve a prender en
  el mismo tick.
- **Los comandos de EconomyCraft aceptan selectores** (`eco addmoney @s 100`)
  porque usan `GameProfileArgument`.
- Para montos que cambian en cada ejecución, usar **macros** con storage
  (`$eco addmoney @s $(monto)`), leyendo el valor con
  `execute store result storage`.

## Cómo verificar que algo quedó bien

No alcanza con que el servidor arranque:

1. `mc.read("/logs/latest.log")` después de cada cambio, buscando excepciones.
2. **Probar sin ser operador** (es la falla que más se nos escapó).
3. Para saber si un comando se ejecuta y dónde muere, intercalar
   `scoreboard players set @s <objetivo> <n>` entre las líneas y leer el score
   después: dice exactamente hasta dónde llegó.
4. Después de tocar precios, **verificar que ningún item se compre más barato de
   lo que se vende**.
5. Correr `servidor/respaldar.py` y commitear.

## Cómo trabajar

- Español rioplatense, de vos. Comentarios en el código en español, explicando
  **por qué** algo es así y no qué hace la línea.
- Alcance mínimo: nada de fallbacks "por si acaso", nada de sistemas de respaldo
  que no pedí. Si algo no se puede hacer bien, decilo en vez de dejar una
  versión a medias.
- Investigá con datos antes de afirmar. Leé los jars, los logs y el código
  fuente de los mods en GitHub en vez de suponer.
- Avisá antes de reiniciar el servidor: casi siempre hay gente jugando.
