# Lo que vive en el servidor

Copia de respaldo de la configuración que hoy solo existe dentro del servidor de
Minehost. Si el mundo se pierde o hay que rearmar el servidor, esto se vuelve a
subir tal cual y todo queda como estaba.

| Script | Para qué |
|---|---|
| `respaldar.py` | Baja del servidor todo lo que mantenemos nosotros. |
| `subir-datapack.py` | Sube el datapack entero (funciones, advancements, menús) y recarga. |
| `generar-precios.py` | Arma `prices.json` y `config.json` de EconomyCraft, rearma el mod cliente de precios y verifica que no haya plata infinita. |
| `verificar-precios.py` | Solo la verificación, contra el servidor o contra un archivo. |
| `generar-menus.py` | Arma los menús de cofre (los deja en el datapack). |
| `generar-comandos.py` | Arma los comandos propios de Melius y los sube. |
| `generar-cartel.py` | Arma el cartel de la derecha. |
| `configurar-scoreboard.py` | Rehace los objetivos y los lugares del scoreboard, que el juego guarda dentro del mundo. |
| `estilo.py` | Los colores y los símbolos, en un solo lugar. |

Las credenciales salen de `web/.env.local`, que no está en el repositorio.

Nada de esto se instala en las máquinas de los jugadores: son mods y datapacks
de servidor, así que se aplican sin publicar una versión nueva del launcher. La
única excepción es el mod de precios, que sí es de cliente — ver más abajo.

## Cómo funciona la economía

Hay **dos monedas que no se cambian entre sí**, igual que en DonutSMP.

|  | Plata | Shards |
|---|---|---|
| Cómo se gana | vender al servidor, comerciar, matar (te llevás el 10% de la plata del muerto) | 10 por matar a un jugador, 1 cada 10 minutos jugados |
| Para qué sirve | consumibles en `/shop`, comerciar en `/ah` y `/orders` | spawners, armas, armaduras, herramientas, pociones y recompensas |
| Se compra con la otra | no | no |

**La tienda del servidor no vende nada durable.** Las categorías `armor`,
`weapons`, `tools` y `enchantments` están apagadas para la compra, y los items
durables sueltos (netherita, elytra, beacon, nether star, maza, huevo de dragón)
tienen `unit_buy: 0`. Todo eso se sigue pudiendo **vender**: apagar una
categoría solo la saca del `/shop`, el `/sell` nunca mira si está habilitada.

Lo que sí se compra barato son los **consumibles de pelea** — totems, gapples,
perlas, obsidiana, crystals, respawn anchors. Eso es lo que hace DonutSMP a
propósito: si regearse cuesta horas, nadie sale a buscar pelea. Es la
distinción que importa: **consumible sí, durable no.**

### La trampa de los precios de Donut

Los números que circulan de DonutSMP (netherite ingot 3,5-6 millones, elytra
250-357 millones) son del **mercado entre jugadores**, no de lo que paga su
`/sell`. Su `/sell` real está en
[donut-quant](https://github.com/Aeripsen/donut-quant) (`quant/worth_table.csv`,
137 items sacados de 158 capturas del GUI de `/worth` in-game, 2026-09-02) y es
otra cosa completamente:

| Relación | En su mercado | En su `/sell` |
|---|---|---|
| elytra / netherite ingot | 59x | **1,2x** |
| netherite ingot / diamante | 912x | **208x** |

O sea que "una elytra vale 85 veces un ingot de netherita" es cierto del
mercado y falso del `/sell`. Nuestra tabla copia las relaciones del **`/sell`**,
que es lo comparable con el nuestro.

Del `/sell` de Donut se copian solo los items de fin del juego. El resto de su
tabla está deformada por su propia meta de farms — les vale el vidrio 70 veces
más que a nosotros y el redstone 35 veces más — y copiarla entera rompía la
coherencia con los otros 1.550 items.

### Las tres formas de sacar plata infinita

`verificar-precios.py` las busca todas, leyendo las 1.515 recetas del jar del
juego. **Correlo después de cada cambio de precios.**

1. **Un item que se venda por más de lo que se compra.** Es la obvia y era la
   única que estaba controlada.
2. **Craftear comprando los ingredientes.** Si todos los ingredientes de una
   receta se venden en la tienda y el resultado se vende por más que la suma,
   es plata garantizada sin riesgo. Es lo que hundió la economía de Donut: allá
   un log de madera cuesta $72 en las órdenes y crafteado en 8 slabs vale $96
   en el `/sell`, o sea 30% seguro, escalable con autocrafters hasta $200M/hora.
   **La tabla de fábrica de EconomyCraft tenía 43 de estas máquinas**, y la peor
   era el lodestone: en 26.1 se craftea con 8 ladrillos de piedra cincelada y
   **un lingote de hierro** (antes era netherita), o sea 31 de ingredientes, y
   se vendía a 257.
3. **El bloque comprimido que vale más que sus nueve unidades.** Esto el script
   lo reporta como aviso y no como falla: comprimir para vender mejor no crea
   plata, porque las unidades hay que conseguirlas igual.

Nunca poner un **multiplicador de venta** que suba con el volumen. Es
exactamente lo que rompió Donut: los jugadores compraban en las órdenes por
debajo de `precio_base x multiplicador` y le vendían al servidor. Uno solo llegó
a vender 15 billones así, y Donut eliminó el sistema entero el 2026-06-02. Por
eso `dynamic_prices_enabled` queda en `false`.

## Los shards

Un objetivo de scoreboard llamado `Shards`, que es lo único que se puede
verificar de verdad con comandos.

- **+10 al matar a otro jugador.** Se paga en `sdp:tick` y no en el advancement,
  porque recién en el tick se sabe quién murió: matarse con la propia flecha
  también dispara el advancement, y así nadie cobra por su propia muerte.
- **+1 cada 10 minutos jugados**, y el tiempo AFK no cuenta. El juego ya lleva
  el contador de ticks de cada jugador con el criterio
  `minecraft.custom:minecraft.play_time`, así que no hace falta contar ticks a
  mano: `sdp_tiempo` los cuenta gratis y `sdp_marca` guarda cuántos había la
  última vez que se pagó. Cuando la resta llega a 12.000, `sdp:turno` compara la
  posición del jugador con la de hace diez minutos y solo paga si se movió.
- **No se pierden al morir ni se pueden pasar a otro jugador.** Si se pudieran
  pasar, dejarían de ser una segunda moneda al instante.

El estado AFK de Essential Commands **no se puede leer desde un datapack**: es
un `private boolean` en memoria y el único placeholder que registra el mod es
`essentialcommands:nickname`. De ahí que la detección sea por posición. Leer la
posición es caro (el juego serializa la entidad entera), pero acá se hace dos
veces por jugador cada diez minutos, así que no se nota.

Los precios de la tienda de shards son los de Donut escalados por el spawner:
allá sale 1.500 y acá 200, o sea todo por 0,133. Lo que se mantiene es la
relación entre los items, que es la que define qué conviene comprar primero.

## `/bounty` se paga en shards, y por qué

Porque **con la plata no se puede hacer bien**. `eco removemoney` devuelve éxito
tanto si cobra como si no le alcanza (hace `sendFailure` y después `return 1`),
`eco pay` hace lo mismo, y no existe ningún comando que lea el saldo: el único
objetivo de scoreboard del mod es `eco_balance`, que solo tiene el top 5 y
escalado a la milésima. Antes de este cambio `/bounty` estaba roto en las dos
direcciones: a un operador le publicaba la recompensa **sin cobrarle** (plata de
la nada) y a un jugador sin OP no le funcionaba nunca, aunque tuviera millones.

Los shards son un score, así que `execute if score @s Shards matches N..` dice
la verdad, y el pago al asesino es una sola operación de scoreboard.

## Los comandos de EconomyCraft y el nivel de operador

`PermissionCompat.gamemaster()` devuelve `true` cuando la fuente **no es un
jugador**, y si es un jugador exige estar en `ops.json`. **El nivel de operador
no le importa**, así que `op_level: 4` de Melius no sirve para nada acá.

Medido en el servidor, con un jugador sin OP:

| Cómo se llama a `eco addmoney` | Anda |
|---|---|
| Melius, `as_console: false`, `@s` | no |
| Melius, `as_console: true`, `@s` | no |
| Melius, `as_console: true`, nombre del jugador | no |
| Melius, `as_console: false`, nombre del jugador | no |
| función de datapack, línea estática, `@a[tag=...]` | **sí** |
| función de datapack, línea de macro, `@a[tag=...]` | **sí** |
| función de datapack, `@s` (estática o macro) | no |
| acción `command` de Inventory Menu con `as_player: false` | **sí** |

Dos reglas salen de ahí:

1. **Los comandos de EconomyCraft van adentro de una función de datapack o de
   una acción de Inventory Menu**, nunca en un comando de Melius. En los dos
   casos la fuente no tiene entidad de jugador y el chequeo pasa siempre.
2. **Nunca `@s`.** Al jugador se lo nombra con `@a[tag=...,limit=1]` en el
   datapack o con `%name%` en Inventory Menu. `@s` no resuelve porque las
   líneas de una función se parsean con una fuente sin entidad — y una macro
   también, aunque se ejecute más tarde.

Esto anda por un `catch` de `getPlayerOrException()`. Si algún día ReaZip lo
cambia por `return false`, todos los `eco` del datapack dejan de compilar de
golpe y en silencio.

## `comandos/` → `/config/melius-commands/commands/`

`/comandos`, `/tienda`, `/economia`, `/casa`, `/pvp`, `/extras`, `/shards`,
`/bounty`, `/nv`, `/nightvision`, `/clearchat`. Desde que los menús son GUI,
casi todos son una línea: abren un menú o llaman a una función.

Los hace **Melius Commands** y se recargan con `/reload`. El esquema completo de
un archivo son seis campos: `id`, `literals`, `arguments`, `require`, `executes`
y `redirect`.

**Cada ejecución necesita `"op_level": 4` explícito.** En Melius ese campo no
tiene valor por defecto: sin él el comando corre con el nivel del jugador, y
`function`, `tellraw` y `scoreboard` piden nivel 2. A un operador le funciona y
a un viewer no, y como `silent` **sí** viene en `true` por defecto, el error no
se ve en ninguna parte: al viewer simplemente no le aparece nada al apretar
enter. Es el tipo de falla que solo se nota si se prueba sin ser operador
(`deop`, probar, `op`).

`as_console` viene en `true` por defecto, y **no borra la entidad de la fuente**:
solo cambia a dónde van los mensajes.

## `datapack/data/sdp/menu/` → los menús de cofre

Los dibuja **Inventory Menu** (`inventory_menu-1.2.0.jar`), que es server-side
puro: `client_side: unsupported`, sin dependencias más que el loader y el juego,
así que **no hay que publicar nada en el launcher**. Los menús viven en el
datapack y se recargan con `/reload`.

`/menu <id>` lo puede usar cualquiera (`menu_command_permission: 0` en
`config/inventory-menu.json`).

Trampas:

- El tipo de item `navigate` **no se usa**: si se le pone un `model`, el mod
  reemplaza el stack entero y pierde el nombre y la descripción. Va `type:
  "item"` con la acción aparte.
- Los placeholders `%...%` **aplanan el texto y le borran el formato a los
  hijos**: `PlaceholderResolver` hace `getString()` y rearma todo como un
  literal. Por eso los nombres y las descripciones no llevan ninguno, y el saldo
  de shards se muestra en el cartel de la derecha en vez de en el menú.
- El item del menú **no se valida al cargar** (`DeferredItemStack` guarda el
  JSON crudo): si el id o un componente están mal, el menú carga igual y en el
  slot aparece una barrera que dice "Invalid menu item". Lo que sí se valida es
  la estructura del menú, y ahí el mod avisa con
  `Error while reading file resource: sdp:menu/<archivo>`.
- `action_cost` de tipo `score` es lo que cobra los shards: el mod verifica el
  score y lo descuenta él, así que no hay forma de comprar sin pagar.

## `cartel/` → `/config/styled-sidebars/styles/`

El cartel de la derecha (**Styled Sidebars**). Se recarga con
`/styledsidebars reload`, **no** con `/reload`.

La forma es la del scoreboard clásico de DonutSMP: etiqueta a la izquierda,
valor a la derecha, un icono por fila. La alineación **no** se hace con
espacios: cuando una línea es un array de dos strings, el mod manda la parte
derecha como el "score" de la fila y el cliente la dibuja pegada al borde.

Trampas:

- **14 líneas visibles.** Si se pasa, el mod empieza a scrollear solo.
- Un array de **un** elemento no es una línea normal: el texto se va a la
  derecha y la izquierda queda vacía.
- Los degradés (`<gr:#aabbcc:#ddeeff>`) **no pueden envolver un placeholder**:
  necesitan texto fijo. El degradé va en el título.
- `%player:objective X%` no formatea los miles y, si el jugador no tiene score
  en ese objetivo, devuelve el literal `[Invalid objective!]`. Por eso
  `sdp:tick` corre `scoreboard players add @a Shards 0` y lo mismo con `Bounty`
  y `sdp_marca`: cualquier objetivo nuevo que se ponga en el cartel necesita su
  inicializador.
- Un solo archivo de estilo mal hecho **deja sin cartel a todos**: el loader
  captura solo `IOException`, así que un JSON inválido se escapa, apaga el mod
  entero y `/styledsidebars reload` responde en rojo.
- Los códigos `&a` no se interpretan, y `<hover>` y `<click>` parsean pero no
  hacen nada: la sidebar no es texto interactivo.

Los colores de los números son los de Donut, que están triangulados entre dos
configs de plugins réplica y el muestreo de píxeles de una captura real: verde
`#00ff00` la plata, violeta `#a503fc` los shards, rojo `#ff0000` las kills,
naranja `#fc7703` las muertes, amarillo `#ffe600` el tiempo. Lo que **no** se
copia es su color de marca: el de Donut es azul `#00a6ff` sobre negro, y este
servidor es dorado.

## `datapack/` → `/world/datapacks/sobrinosdepepe/`

Las recompensas, los shards, la visión nocturna y los menús.

Cuando un jugador mata a otro, el advancement marca al asesino y la función de
tick cruza esa marca con quién murió: el asesino y la muerte ocurren en el mismo
tick pero sin un orden garantizado, así que se resuelven al final del tick en vez
de confiar en cuál pasa primero.

`pack.mcmeta` en 26.1 lleva **solo `min_format` y `max_format`, y el formato es
101**. Sale del `version.json` del propio juego: `data_major: 101,
data_minor: 1`. El archivo decía 81, que es el formato de 1.21.7/1.21.8.
Medido: a un datapack de mundo **ya habilitado** el juego no le revalida el
formato, así que con 81 andaba igual — pero si algún día hay que rearmar el
mundo, con el número viejo el pack podría no cargar. Desde el formato 82 en
adelante `pack_format` y `supported_formats` **no están permitidos** y hay que
borrarlos.

También vive acá la visión nocturna (`/nv`). El mismo comando la prende y la
apaga: `nv.mcfunction` corta con `return run` antes de la segunda línea, porque
si no, apagarla dejaría la marca en cero y la línea siguiente la volvería a
prender en el mismo tick. La marca guarda la intención del jugador y la función
de tick repone el efecto a quien lo perdió al morir, mirando el predicado
`tiene_nv` para no reaplicarlo cada tick a quien ya lo tiene.

## El mod cliente de precios

`mod-precios/` dibuja "Precio: $N" en la descripción de cada item, y **los
precios viajan adentro del jar**. Si cambian los precios del servidor y no se
rearma el mod, los cartelitos mienten.

`generar-precios.py` lo rearma solo y **no hace falta compilar nada**:
`precios.json` es un recurso del jar y se reemplaza dentro del zip, dejando la
clase intacta. Eso importa porque para compilarlo hace falta un JDK 25 y en esta
PC no hay ninguno (solo un JRE 17 y el JRE 25 que baja el launcher).

El jar nuevo queda en `mod-precios/build/libs/` y **hay que publicarlo desde el
panel** para que llegue a los jugadores. Eso los obliga a actualizar, así que
conviene hacerlo cuando no haya nadie jugando.

## Un error conocido en el log

Al recargar o cuando entra alguien, el log escupe varios
`WrongMethodTypeException` desde `eu.pb4.predicate`. Es un bug de copiar y
pegar en `FabricPermissionBridge` de la `predicate-api 0.8.1`: su
`findCheckPermission()` asigna **siempre** a `permissionCheckCallCommandLevel`,
sin importar qué método buscó, así que después del bloque estático ese campo
apunta a `checkPermission(Identifier, boolean)` y cualquier llamada con un
`PermissionLevel` explota. El `catch` lo agarra, imprime el stack trace y cae a
LuckPerms, así que la respuesta sale bien y es solo ruido.

La consecuencia práctica: un predicado `{"type": "permission"}` **con** el campo
`operator` pasa por el camino roto. Sin ese campo usa la otra sobrecarga y no
explota. Aun así conviene usar `{"type": "operator", "operator": 4}`, que es lo
que ya está probado acá y no toca la librería.

No hay versión más nueva de Melius ni de Styled Sidebars para 26.1, así que se
resolvió por afuera: `modificadores/styledsidebars.json` reemplaza el requisito
de ese comando por `{"type": "operator", "operator": 4}`.

Lo peor de esto es cómo se veía: como el chequeo cortaba por lo alto cuando el
jugador era operador, a quien administra el servidor le funcionaba todo y a los
demás no les aparecía nada, sin ningún error visible en el juego.

## `/clear` y `/clearchat`

`/clear` le vacía el inventario a quien lo escribe y el nombre invita a pensar
que limpia el chat. `modificadores/clear.json` lo deja solo para nivel 4 y
`/clearchat` hace lo que la gente busca. Un operador todavía puede escribir
`/clear` y borrarse el inventario: para eso no hay red de contención.

## Otras cosas de 26.1 que ya nos costaron tiempo

- **Los símbolos van como `\uXXXX` dentro del JSON.** Una barra invertida suelta
  en un heredoc del shell termina siendo un salto de línea real adentro del
  comando y lo parte al medio; y un símbolo literal escrito en un heredoc **no
  llega igual** del otro lado. Los scripts los escriben con `chr()` y los
  `.mcfunction` quedan en ASCII puro.
- **Las gamerules son `snake_case`.** `max_command_sequence_length`,
  `keep_inventory`, `advance_time`, `send_command_feedback`, `show_death_messages`.
- **`schedule` acepta `t`, `s` y `d`, no `m`.** Diez minutos son `12000t`.
- **`minecraft.custom:minecraft.play_one_minute` no existe** desde 1.17. Es
  `play_time`, y cuenta en ticks: medido, sube 604 en 30 segundos.
- **Un objetivo con criterio de estadística arranca en cero** cuando se crea y
  suma desde ahí; no se le puede resetear el total, porque el juego le vuelve a
  escribir el valor absoluto en cuanto la estadística cambia.
- **`execute store result` con `data get` trunca hacia abajo**, no redondea.
- **Los componentes de item se validan al parsear** el comando, pero el NBT de
  adentro de `block_entity_data` no. Medido: un componente inexistente o un
  encantamiento inexistente dan error, pero
  `spawner[block_entity_data={id:"minecraft:chest"}]` pasa sin chistar.
- **El spawner con mob adentro** es
  `spawner[block_entity_data={id:"minecraft:mob_spawner",SpawnData:{entity:{id:"minecraft:skeleton"}}}]`.
  Verificado poniendo el bloque y leyéndolo: el juego completa `SpawnPotentials`
  solo.
- **`enchantments` ya no lleva el envoltorio `levels`**: es
  `enchantments={sharpness:5}` directo. `unbreakable={}` tampoco lleva
  `show_in_tooltip`.
- **En `tellraw` los eventos son `click_event` / `hover_event`** con `command` /
  `value`, y el slot del scoreboard es `below_name`, no `belowName`.
- **`/reload` recarga los datapacks, los menús de cofre y los comandos de
  Melius, pero NO el cartel** (`/styledsidebars reload`) **ni la configuración
  de EconomyCraft** (esa pide reinicio, y no tiene comando de reload).
- **`dailySellLimit` es todo-o-nada por operación**, no un tope que se llena: si
  al jugador le quedan 500 de margen y quiere vender algo de 600, se le rechaza
  la venta completa. Por eso está en 250.000 y no en 10.000: con los precios
  nuevos un ingot de netherita vale 17.500 y con el límite viejo no se podía
  vender ni uno.
- **`scoreboard_enabled` de EconomyCraft tiene que quedar en `false`**: si se
  prende, el mod crea el objetivo `eco_balance` y se apropia del lugar del
  cartel. Y al volver a apagarlo **borra** ese objetivo del mundo.
- **26.1 movió las carpetas del mundo**: `data/scoreboard.dat` pasó a
  `data/minecraft/scoreboard.dat`, `stats/` a `players/stats/`, `playerdata/` a
  `players/data/`.
- **`balances.json` se escribe asincrónico** desde un mapa en memoria: editarlo a
  mano con el servidor prendido no sirve, el próximo guardado lo pisa.
- **Vender está bloqueado en silencio por daño y por contenido**: cualquier
  herramienta usada y cualquier shulker o bundle con cosas adentro no se pueden
  vender. Al jugador le va a parecer un bug del servidor y no una regla.

## Cómo verificar que algo quedó bien

No alcanza con que el servidor arranque.

1. `mc.read("/logs/latest.log")` después de cada cambio, buscando excepciones.
2. **Probar sin ser operador.** Es la falla que más se nos escapó. Con un
   jugador conectado que no sea OP, `execute as <jugador> run <comando>` desde
   la consola reproduce exactamente las condiciones de Melius: la fuente queda
   con la entidad de ese jugador.
3. Para saber si un comando se ejecuta y dónde muere, intercalar
   `scoreboard players set @s <objetivo> <n>` entre las líneas y leer el score
   después: dice exactamente hasta dónde llegó. Si el score queda **sin
   asignar** en vez de en cero, el comando no llegó ni a parsear.
4. `python servidor/verificar-precios.py` después de tocar precios.
5. Correr `servidor/respaldar.py` y commitear.
