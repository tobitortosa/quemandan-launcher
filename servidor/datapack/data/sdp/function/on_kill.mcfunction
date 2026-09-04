# Marca al asesino durante este tick. Quien murio se sabe recien en sdp:tick,
# porque el orden de los dos eventos dentro del mismo tick no es fiable.
scoreboard players set @s sdp_killer 1
advancement revoke @s only sdp:kill
