scoreboard players set @s sdp_nv 1
effect give @s night_vision infinite 1 true
tellraw @s ["", {"text": "\n  \u263d ", "color": "aqua"}, {"text": "Vision nocturna activada", "color": "aqua", "bold": true}, {"text": "\n  Escribi ", "color": "gray"}, {"text": "/nv", "color": "white"}, {"text": " de nuevo para sacarla.\n", "color": "gray"}]
playsound minecraft:block.beacon.activate master @s ~ ~ ~ 0.3 1.8
