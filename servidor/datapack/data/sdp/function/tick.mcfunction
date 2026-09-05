# Si murio alguien que tenia precio en su cabeza, se le paga a quien lo mato.
# El diseno asume una muerte por tick: con dos en el mismo tick, el limit=1 de
# sdp:cobrar puede emparejar mal. Con cuatro jugadores no pasa nunca.
execute as @a[scores={sdp_death=1..,Bounty=1..}] run function sdp:cobrar

# Shards por matar. Se paga aca y no en el advancement porque el advancement no
# dice a quien mato, y el asesino se marca en el mismo tick que la muerte.
execute as @a[scores={sdp_killer=1}] run function sdp:shard_kill

# El contador de muertes se reinicia todos los ticks: solo interesa este.
scoreboard players reset * sdp_death
scoreboard players reset * sdp_killer

# Deja el precio en cero a quien no tenga, para que el cartel muestre algo.
# %player:objective% se cae si el jugador no tiene score en el objetivo.
scoreboard players add @a Bounty 0
scoreboard players add @a Shards 0

# Al que todavia no tiene turno asignado se le fija el primero y se le guarda la
# posicion, para que el primer shard no sea de regalo.
execute as @a unless score @s sdp_marca matches 1.. run function sdp:empezar

# Shards por tiempo. sdp_tiempo lo cuenta el juego solo (criterio play_time) y
# sdp_marca guarda en que tick jugado toca el proximo shard.
#
# La comparacion va con @s a los dos lados a proposito. Con @a NO anda, y lo
# peor es que no falla: scoreboard players operation recorre las dos colecciones
# anidadas, asi que cada jugador termina con el valor del ultimo de la lista y,
# en la resta, con la suma de todos. Medido en el servidor: con dos conectados
# los shards por tiempo dejaron de pagarse; con uno solo andaba perfecto.
execute as @a if score @s sdp_tiempo >= @s sdp_marca run function sdp:turno

# Repone la vision nocturna a quien la dejo prendida y la perdio al morir.
execute as @a[scores={sdp_nv=1}] unless predicate sdp:tiene_nv run effect give @s night_vision infinite 1 true
