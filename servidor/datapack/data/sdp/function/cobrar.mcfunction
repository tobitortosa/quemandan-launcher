# @s es quien murio con precio en la cabeza.

# Sin asesino no hay pago: si se cayo al vacio, la recompensa sigue en pie.
execute unless entity @a[scores={sdp_killer=1}] run return 0

# Nadie cobra su propia cabeza: matarse solo no paga.
execute if entity @s[scores={sdp_killer=1}] run return 0

tag @s add sdp_cazado
tag @a[scores={sdp_killer=1},limit=1] add sdp_cobra

# La recompensa se paga en shards y no en plata porque los shards son un score:
# se pueden verificar y mover con comandos. Con la plata no se puede, porque
# EconomyCraft devuelve exito tanto si cobra como si no le alcanza.
scoreboard players operation @a[tag=sdp_cobra,limit=1] Shards += @s Bounty
function sdp:anunciar_bounty
scoreboard players set @s Bounty 0

tag @s remove sdp_cazado
tag @a remove sdp_cobra
