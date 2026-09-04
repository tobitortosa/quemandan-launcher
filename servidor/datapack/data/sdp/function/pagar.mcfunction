# @s es el asesino. El monto viene por macro porque cambia en cada muerte.
$eco addmoney @s $(monto)
tellraw @a ["", {"text": "\n  \u2620 ", "color": "red", "bold": true}, {"selector": "@s", "color": "green", "bold": true}, {"text": " cobro la recompensa de ", "color": "gray"}, {"selector": "@a[tag=sdp_cazado,limit=1]", "color": "red", "bold": true}, {"text": "\n     y se llevo ", "color": "gray"}, {"text": "$", "color": "gold", "bold": true}, {"score": {"name": "@a[tag=sdp_cazado,limit=1]", "objective": "Bounty"}, "color": "gold", "bold": true}, {"text": "\n", "color": "gray"}]
playsound minecraft:entity.player.levelup master @a ~ ~ ~ 1 1.2
