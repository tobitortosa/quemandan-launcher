# -*- coding: utf-8 -*-
"""
Deja los objetivos y los lugares del scoreboard como tienen que estar.

    python servidor/configurar-scoreboard.py

Esto no vive en ningún archivo de configuración: el juego lo guarda dentro del
mundo (world/data/scoreboard.dat). Si algún día hay que rearmar el servidor o se
pierde el mundo, se corre esto y queda igual.

Los tres lugares que tiene el juego:
  - sidebar     el cartel de la derecha, que maneja Styled Sidebars por su cuenta
  - list        la tabla del TAB
  - below_name  debajo del nombre del jugador, en el mundo
"""
import json

import mc

CORAZON = chr(0x2764)

OBJETIVOS = [
    # nombre, criterio, como se muestra
    ("HP", "health", {"text": CORAZON, "color": "red"}),
    ("Bounty", "dummy", {"text": chr(0x2620) + " Recompensa", "color": "red"}),
    ("sdp_death", "deathCount", {"text": "muertes del tick"}),
    ("sdp_killer", "dummy", {"text": "asesino del tick"}),
    ("sdp_ok", "dummy", {"text": "resultado del cobro"}),
    ("sdp_nv", "dummy", {"text": "vision nocturna"}),
]

for nombre, criterio, display in OBJETIVOS:
    # Si ya existe, el comando falla sin consecuencias.
    mc.cmd("scoreboard objectives add %s %s %s" % (nombre, criterio, json.dumps(display)))
    print("  objetivo %s (%s)" % (nombre, criterio))

# La vida se dibuja como corazones y no como numero.
mc.cmd("scoreboard objectives modify HP rendertype hearts")

# La vida de todos en el TAB, y tambien sobre la cabeza de quien tenes enfrente.
mc.cmd("scoreboard objectives setdisplay list HP")
mc.cmd("scoreboard objectives setdisplay below_name HP")
print("  TAB y sobre la cabeza: corazones")
