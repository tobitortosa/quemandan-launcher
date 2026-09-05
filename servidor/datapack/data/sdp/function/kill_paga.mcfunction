# @s es el muerto, y sdp_asesino esta puesto en quien lo mato.

# 12000 ticks son diez minutos. Es lo unico que separa una pelea de una maquina
# de shards: matar de nuevo a la misma persona antes de eso no paga.
scoreboard players set @s sdp_cd 12000

execute as @a[tag=sdp_asesino] run function sdp:shard_kill
