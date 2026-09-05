# @s es quien acaba de morir.
#
# El pago de la kill se hace DESDE la victima y no desde el asesino, aunque el
# que cobra sea el asesino. Es la unica forma de mirar el enfriamiento de esta
# victima en particular, y sin eso dos amigos se matan en loop y los shards
# salen de la nada: respawnear desnudo al lado del otro y volver a morir no
# cuesta nada, y son 10 shards por vuelta contra los 144 por dia que paga el
# tiempo jugado.
#
# De paso arregla algo que el pago por asesino hacia mal: si alguien mataba a
# dos en el mismo tick cobraba una sola vez, porque sdp_killer es una marca y no
# una cuenta. Asi cobra una vez por muerto.

tag @s add sdp_muerto

# El asesino no puede ser el propio muerto: si mato a alguien mas en el mismo
# tick, el tambien tiene la marca de asesino.
tag @a[scores={sdp_killer=1},tag=!sdp_muerto,limit=1] add sdp_asesino

# Muerte por mob, por caida o por el vacio: no hay a quien pagarle.
execute unless entity @a[tag=sdp_asesino] run return run tag @s remove sdp_muerto

execute if score @s sdp_cd matches 1.. run function sdp:kill_repetida
execute unless score @s sdp_cd matches 1.. run function sdp:kill_paga

tag @s remove sdp_muerto
tag @a remove sdp_asesino
