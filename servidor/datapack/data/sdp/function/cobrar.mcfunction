# @s es quien murio con precio en la cabeza.

tag @s add sdp_cazado

# El asesino no puede ser el propio muerto. Suicidarse NO dispara el advancement
# (ServerPlayer.awardKillScore arranca con "if (victim != this)"), pero si el
# muerto habia matado a alguien mas en el mismo tick tambien tiene la marca de
# asesino, y con limit=1 podria cobrar su propia cabeza.
tag @a[scores={sdp_killer=1},tag=!sdp_cazado,limit=1] add sdp_cobra

# Sin asesino no hay pago: si se cayo al vacio, la recompensa sigue en pie.
execute unless entity @a[tag=sdp_cobra] run return run tag @s remove sdp_cazado

# La recompensa se paga en shards y no en plata porque los shards son un score:
# se pueden verificar y mover con comandos. Con la plata no se puede, porque
# EconomyCraft devuelve exito tanto si cobra como si no le alcanza.
scoreboard players operation @a[tag=sdp_cobra,limit=1] Shards += @s Bounty
function sdp:anunciar_bounty
scoreboard players set @s Bounty 0

tag @s remove sdp_cazado
tag @a remove sdp_cobra
