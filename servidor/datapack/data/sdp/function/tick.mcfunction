# Si murio alguien que tenia precio en su cabeza, se le paga a quien lo mato.
execute as @a[scores={sdp_death=1..,Bounty=1..}] run function sdp:cobrar

# Shards por matar. Se paga aca y no en el advancement porque recien en el tick
# se sabe quien murio: matarse con la propia flecha tambien dispara el
# advancement, y asi nadie cobra por su propia muerte.
execute as @a[scores={sdp_killer=1}] unless score @s sdp_death matches 1.. run function sdp:shard_kill

# El contador de muertes se reinicia todos los ticks: solo interesa este.
scoreboard players reset * sdp_death
scoreboard players reset * sdp_killer

# Deja el precio en cero a quien no tenga, para que el cartel muestre algo.
# %player:objective% se cae si el jugador no tiene score en el objetivo.
scoreboard players add @a Bounty 0
scoreboard players add @a Shards 0
scoreboard players add @a sdp_marca 0

# Shards por tiempo: sdp_tiempo lo cuenta el juego (criterio play_time) y
# sdp_marca guarda cuanto habia la ultima vez que se pago. La resta se hace con
# operaciones sobre @a en vez de una funcion por jugador porque corre cada tick.
scoreboard players operation @a sdp_dif = @a sdp_tiempo
scoreboard players operation @a sdp_dif -= @a sdp_marca
execute as @a[scores={sdp_dif=12000..}] run function sdp:turno

# Repone la vision nocturna a quien la dejo prendida y la perdio al morir.
execute as @a[scores={sdp_nv=1}] unless predicate sdp:tiene_nv run effect give @s night_vision infinite 1 true
