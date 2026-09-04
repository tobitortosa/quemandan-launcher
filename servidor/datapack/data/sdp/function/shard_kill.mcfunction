# @s es el asesino del tick.
scoreboard players add @s Shards 10
title @s actionbar ["", {"text": "\u2726 ", "color": "#42d4f5"}, {"text": "+10 shards", "color": "#42d4f5", "bold": true}, {"text": "  por la kill", "color": "gray"}]
playsound minecraft:block.amethyst_block.resonate master @s ~ ~ ~ 1 1.4
