# @s nunca cobro un shard por tiempo: se le fija el primer turno dentro de diez
# minutos y se le guarda la posicion de ahora, asi el primer cobro tambien pasa
# por el chequeo de que se haya movido.
scoreboard players operation @s sdp_marca = @s sdp_tiempo
scoreboard players add @s sdp_marca 12000
execute store result score @s sdp_x run data get entity @s Pos[0] 10
execute store result score @s sdp_z run data get entity @s Pos[2] 10

# Es la primera vez que entra, asi que aca va el unico saludo. El JSON lo
# escribe generar-bienvenida.py: tiene saltos de linea adentro y a mano se
# parte al medio.
tellraw @s ["", {"text": "\n"}, {"text": "  Bienvenido a ", "color": "gray"}, {"text": "SOBRINOS DE PEPE", "color": "#ffb02e", "bold": true}, {"text": "\n\n"}, {"text": "  Todo se abre desde ", "color": "gray"}, {"text": "/ayuda", "color": "#00a6ff", "bold": true, "click_event": {"action": "run_command", "command": "/ayuda"}, "hover_event": {"action": "show_text", "value": {"text": "Clickealo para abrir el menu", "color": "gray"}}}, {"text": "   \u00ab clickealo", "color": "dark_gray"}, {"text": "\n"}, {"text": "  La tienda, tu casa, el PvP y la tienda de shards.", "color": "gray"}, {"text": "\n"}]
playsound minecraft:block.note_block.chime master @s ~ ~ ~ 1 1.2
