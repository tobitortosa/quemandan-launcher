# Lo que vive en el servidor

Copia de respaldo de la configuración que hoy solo existe dentro del servidor de
Minehost. Si el mundo se pierde o hay que rearmar el servidor, esto se vuelve a
subir tal cual y todo queda como estaba.

Nada de esto se instala en las máquinas de los jugadores: son mods y datapacks
de servidor, así que se aplican sin publicar una versión nueva del launcher.

## `comandos/` → `/config/melius-commands/commands/`

El menú de `/comandos` y sus categorías (`/economia`, `/casa`, `/pvp`,
`/extras`), más `/bounty`. Los hace **Melius Commands**: cada archivo declara un
comando y los `tellraw` que ejecuta. Los comandos que tocan la economía corren
con `op_level: 4` y `as_console: false`, para que `@s` sea el jugador pero tenga
permiso de mover plata.

Después de cambiar un archivo, `/reload` en el juego los vuelve a leer.

## `cartel/` → `/config/styled-sidebars/styles/`

El cartel de la derecha (**Styled Sidebars**): dinero, kills, muertes y el
precio que tiene tu cabeza. Los valores salen de placeholders —
`%economycraft:balance_formatted%` para la plata,
`%player:statistic_raw player_kills%` para las kills (que arrancan con el
historial real de cada uno) y `%player:objective Bounty%` para la recompensa.

Se recarga con `/styledsidebars reload`, **no** con `/reload`.

## `datapack/` → `/world/datapacks/sobrinosdepepe/`

Las recompensas. Cuando un jugador mata a otro, el advancement marca al asesino
y la función de tick cruza esa marca con quién murió: el asesino y la muerte
ocurren en el mismo tick pero sin un orden garantizado, así que se resuelven al
final del tick en vez de confiar en cuál pasa primero.

`pack.mcmeta` declara los cuatro campos de versión (`pack_format`,
`supported_formats`, `min_format`, `max_format`) y **tienen que coincidir entre
sí**: 26.1 rechaza el pack si uno dice 17 y el otro 81.
