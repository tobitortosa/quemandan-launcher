# La lista de buscados. El tag marca a quien pidio la lista para que el
# tellraw de adentro del execute le llegue solo a el.
tag @s add sdp_viendo
tellraw @s ["", {"text": "\n\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac  \u2620 BUSCADOS  \u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\n\n", "color": "#ff00a6", "bold": true}]
execute unless entity @a[scores={Bounty=1..}] run tellraw @s ["", {"text": "   No hay nadie con precio en su cabeza.\n", "color": "gray"}]
execute as @a[scores={Bounty=1..}] run tellraw @a[tag=sdp_viendo] ["", {"text": "   \u2620 ", "color": "#ff00a6"}, {"selector": "@s", "color": "white", "bold": true}, {"text": "  \u00bb  ", "color": "dark_gray"}, {"text": "\u2726", "color": "#a503fc"}, {"score": {"name": "@s", "objective": "Bounty"}, "color": "#a503fc", "bold": true}, {"text": "\n"}]
tellraw @s ["", {"text": "\n  Para poner precio: ", "color": "dark_gray"}, {"text": "/bounty <jugador> <shards>", "color": "#00a6ff"}, {"text": "\n\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\u25ac\n", "color": "#ff00a6", "bold": true}]
tag @s remove sdp_viendo
