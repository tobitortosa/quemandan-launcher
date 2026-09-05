# @s nunca cobro un shard por tiempo: se le fija el primer turno dentro de diez
# minutos y se le guarda la posicion de ahora, asi el primer cobro tambien pasa
# por el chequeo de que se haya movido.
scoreboard players operation @s sdp_marca = @s sdp_tiempo
scoreboard players add @s sdp_marca 12000
execute store result score @s sdp_x run data get entity @s Pos[0] 10
execute store result score @s sdp_z run data get entity @s Pos[2] 10
