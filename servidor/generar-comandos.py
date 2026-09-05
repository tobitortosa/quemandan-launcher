# -*- coding: utf-8 -*-
"""
Arma los comandos propios y los sube al servidor.

    python servidor/generar-comandos.py

Los declara Melius Commands. Desde que los menus son GUI de cofre, todos estos
comandos son una linea: abren el menu que corresponde o llaman a una funcion del
datapack.

**Cada ejecucion necesita `op_level: 4` explicito.** En Melius ese campo no
tiene valor por defecto: sin el, el comando corre con el nivel del jugador, y
`function`, `tellraw` y `scoreboard` piden nivel 2. A un operador le funciona y
a un viewer no, y como `silent` viene en `true` por defecto, el error no se ve en
ninguna parte: al viewer simplemente no le aparece nada al apretar enter.

Los simbolos se escriben con chr() y el JSON sale de json.dumps a proposito: una
barra invertida suelta en este archivo termina siendo un salto de linea real
adentro del comando y lo parte al medio.
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import estilo as e
import mc

CARPETA = os.path.join(AQUI, "comandos")


def accion(comando):
    return {"command": comando, "silent": True, "as_console": False, "op_level": 4}


def guardar(cid, doc):
    doc = dict(doc, id=cid)
    texto = json.dumps(doc, indent=2, ensure_ascii=False)
    os.makedirs(CARPETA, exist_ok=True)
    open(os.path.join(CARPETA, cid + ".json"), "w", encoding="utf-8", newline="\n").write(texto)
    mc.write("/config/melius-commands/commands/%s.json" % cid, texto)
    print("  %s" % cid)


def t(texto, color=None, negrita=False, run=None, hover=None):
    c = {"text": texto}
    if color:
        c["color"] = color
    if negrita:
        c["bold"] = True
    if run:
        c["click_event"] = {"action": "run_command", "command": run}
    if hover:
        c["hover_event"] = {"action": "show_text", "value": {"text": hover, "color": "gray"}}
    return c


# Los que solo abren un menu.
for cid, menu in [
    # /ayuda es el nombre que se publicita y /comandos queda de alias. Un jugador
    # hispanohablante tipea "/ayuda" sin que nadie le diga nada, y /help ya es del
    # vanilla. /menu no se puede usar: lo registra Inventory Menu y pide un id.
    ("ayuda", "sdp:comandos"),
    ("comandos", "sdp:comandos"),
    ("tienda", "sdp:tienda"),
    ("economia", "sdp:economia"),
    ("casa", "sdp:casa"),
    ("pvp", "sdp:pvp"),
    ("extras", "sdp:extras"),
]:
    guardar(cid, {"executes": [accion("menu " + menu)]})

# Los que llaman a una funcion del datapack.
for cid, funcion in [
    ("nv", "sdp:nv"),
    ("nightvision", "sdp:nv"),
    ("shards", "sdp:shards"),
]:
    guardar(cid, {"executes": [accion("function " + funcion)]})

# El chat limpio son sesenta lineas vacias: no hay comando vanilla que lo haga.
guardar("clearchat", {"executes": [accion(
    "tellraw @s " + json.dumps(["", {"text": chr(10) * 60},
                                t("  Chat limpio." + chr(10), e.APAGADO)]))]})

mc.cmd("reload")
print("  recargado")
