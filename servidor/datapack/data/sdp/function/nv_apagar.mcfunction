scoreboard players set @s sdp_nv 0
effect clear @s night_vision
tellraw @s ["", {"text": "\n  \u263d ", "color": "dark_gray"}, {"text": "Vision nocturna desactivada\n", "color": "gray"}]
playsound minecraft:block.beacon.deactivate master @s ~ ~ ~ 0.3 1.8
