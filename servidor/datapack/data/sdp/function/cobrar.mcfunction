# Sin asesino no hay pago: si se cayo al vacio, la recompensa sigue en pie.
execute unless entity @a[scores={sdp_killer=1}] run return 0

tag @s add sdp_cazado
execute store result storage sdp:tmp monto int 1 run scoreboard players get @s Bounty
execute as @a[scores={sdp_killer=1},limit=1] run function sdp:pagar with storage sdp:tmp
scoreboard players set @s Bounty 0
tag @s remove sdp_cazado
