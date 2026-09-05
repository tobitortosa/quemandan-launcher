# @s cumplio diez minutos de reloj. El shard se paga solo si se movio en ese
# rato: el criterio play_time sigue contando a quien deja el juego abierto sin
# jugar, y el estado AFK de Essential Commands no se puede leer desde aca.
scoreboard players operation @s sdp_marca = @s sdp_tiempo
scoreboard players add @s sdp_marca 12000

# sdp_dif se usa de variable de trabajo para restar contra la posicion guardada.
# Las coordenadas van en decimetros (escala 10) para que cualquier movimiento
# chico ya cuente.
scoreboard players operation @s sdp_dif = @s sdp_x
execute store result score @s sdp_x run data get entity @s Pos[0] 10
scoreboard players operation @s sdp_dif -= @s sdp_x
execute unless score @s sdp_dif matches 0 run tag @s add sdp_movio

scoreboard players operation @s sdp_dif = @s sdp_z
execute store result score @s sdp_z run data get entity @s Pos[2] 10
scoreboard players operation @s sdp_dif -= @s sdp_z
execute unless score @s sdp_dif matches 0 run tag @s add sdp_movio

execute if entity @s[tag=sdp_movio] run function sdp:shard_tiempo
tag @s remove sdp_movio
