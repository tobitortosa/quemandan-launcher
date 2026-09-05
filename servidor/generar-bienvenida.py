# -*- coding: utf-8 -*-
"""
Agrega el saludo de primera entrada a sdp:empezar.

    python servidor/generar-bienvenida.py

Existe como script y no escrito a mano porque el JSON del tellraw lleva saltos
de linea, y una barra invertida suelta pasada por el shell termina siendo un
salto de linea REAL adentro del comando y lo parte al medio. Ya paso: la primera
version de este mensaje quedo repartida en cinco lineas y el datapack no
cargaba. Aca el JSON sale de json.dumps y el salto de linea de chr(10), asi que
no hay ninguna barra invertida escrita a mano.

El saludo va solo en la PRIMERA entrada. El unico gancho vanilla para saludar en
cada reconexion es el criterio leave_game, y tiene un modo de falla feo: si el
jugador todavia no tiene score en ese objetivo, la comparacion contra la copia
falla y el mensaje se repite cada tick, para todos. El cartel de la derecha deja
/ayuda a la vista todo el tiempo, asi que no hace falta.
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import estilo as e

RUTA = os.path.join(AQUI, "datapack", "data", "sdp", "function", "empezar.mcfunction")
SALTO = chr(10)

MENSAJE = ["",
           {"text": SALTO},
           {"text": "  Bienvenido a ", "color": e.ETIQUETA},
           {"text": "SOBRINOS DE PEPE", "color": e.MARCA, "bold": True},
           {"text": SALTO * 2},
           {"text": "  Todo se abre desde ", "color": e.ETIQUETA},
           {"text": "/ayuda", "color": e.ACENTO, "bold": True,
            "click_event": {"action": "run_command", "command": "/ayuda"},
            "hover_event": {"action": "show_text",
                            "value": {"text": "Clickealo para abrir el menu",
                                      "color": e.ETIQUETA}}},
           {"text": "   " + e.VOLVER + " clickealo", "color": e.APAGADO},
           {"text": SALTO},
           {"text": "  La tienda, tu casa, el PvP y la tienda de shards.", "color": e.ETIQUETA},
           {"text": SALTO}]

MARCA = "# Es la primera vez que entra, asi que aca va el unico saludo. El JSON lo"

COMENTARIO = [
    "",
    MARCA,
    "# escribe generar-bienvenida.py: tiene saltos de linea adentro y a mano se",
    "# parte al medio.",
]

if __name__ == "__main__":
    base = open(RUTA, encoding="utf-8").read().rstrip(SALTO)
    # Si ya estaba, se reemplaza en vez de negarse: asi cambiar el texto del
    # saludo es correr el script otra vez y no editar el .mcfunction a mano,
    # que es justo lo que no queremos con un JSON que lleva saltos de linea.
    if MARCA in base:
        base = base[:base.index(MARCA)].rstrip(SALTO)
    lineas = [base] + COMENTARIO + [
        "tellraw @s " + json.dumps(MENSAJE, ensure_ascii=True),
        "playsound minecraft:block.note_block.chime master @s ~ ~ ~ 1 1.2",
        "",
    ]
    texto = SALTO.join(lineas)
    open(RUTA, "w", encoding="ascii", newline=SALTO).write(texto)

    crudo = open(RUTA, "rb").read()
    assert all(b < 128 for b in crudo), "quedo algo que no es ASCII"
    for linea in crudo.decode().splitlines():
        if linea.startswith("tellraw"):
            json.loads(linea[len("tellraw @s "):])
    print("escrito %s (%d lineas, el tellraw entero en una)"
          % (os.path.relpath(RUTA, os.path.dirname(AQUI)), crudo.count(10)))
