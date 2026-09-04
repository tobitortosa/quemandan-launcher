# -*- coding: utf-8 -*-
"""
Arma los comandos propios y los sube al servidor.

    python servidor/generar-comandos.py

Los declara Melius Commands. Desde que los menus son GUI de cofre, casi todos
estos comandos son una linea: abren el menu que corresponde o llaman a una
funcion del datapack. La excepcion es /bounty, que hace toda su cuenta aca.

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

# ---------------------------------------------------------------------- /bounty
# Poner una recompensa se paga en SHARDS y no en plata. Es la unica forma de que
# el chequeo sea correcto: los shards son un objetivo de scoreboard, asi que
# `execute if score` dice de verdad si alcanza. Con la plata no se puede, porque
# `eco removemoney` devuelve exito tanto si cobra como si no le alcanza, y no hay
# ningun comando que lea el saldo.
aviso_sin_shards = ["", t("  " + e.CRUZ + " ", e.ERROR),
                    t("No te alcanzan los shards para esa recompensa.", e.ERROR),
                    t(chr(10))]

anuncio = ["",
           t(chr(10) + "  " + e.CALAVERA + " RECOMPENSA " + e.CALAVERA + chr(10),
             e.RECOMPENSA, negrita=True),
           t("  ", e.ETIQUETA), {"selector": "@s", "color": e.MARCA, "bold": True},
           t(" puso ", e.ETIQUETA),
           t(e.SHARD + "${monto}", e.SHARDS, negrita=True),
           t(" shards por la cabeza de" + chr(10) + "  ", e.ETIQUETA),
           {"selector": "${objetivo}", "color": e.RECOMPENSA, "bold": True},
           t(chr(10) * 2 + "  Total acumulado: ", e.ETIQUETA),
           t(e.SHARD, e.SHARDS),
           {"score": {"name": "${objetivo}", "objective": "Bounty"},
            "color": e.SHARDS, "bold": True},
           t("   " + e.FLECHA + "  ", e.APAGADO),
           t("/bounty", e.ACENTO, run="/bounty", hover="Ver la lista de buscados"),
           t(" para ver la lista" + chr(10), e.ETIQUETA)]

guardar("bounty", {
    "executes": [accion("function sdp:lista_bounty")],
    "arguments": [{
        "id": "objetivo",
        "type": "minecraft:entity player",
        "arguments": [{
            "id": "monto",
            "type": "brigadier:integer 10",
            "executes": [
                accion("execute store success score @s sdp_ok "
                       "if score @s Shards matches ${monto}.."),
                accion("execute if score @s sdp_ok matches 1 run "
                       "scoreboard players remove @s Shards ${monto}"),
                accion("execute if score @s sdp_ok matches 1 run "
                       "scoreboard players add ${objetivo} Bounty ${monto}"),
                accion("execute if score @s sdp_ok matches 1 run tellraw @a "
                       + json.dumps(anuncio)),
                accion("execute if score @s sdp_ok matches 1 run "
                       "playsound minecraft:entity.wither.spawn master @a ~ ~ ~ 0.4 1.6"),
                accion("execute if score @s sdp_ok matches 0 run tellraw @s "
                       + json.dumps(aviso_sin_shards)),
                accion("scoreboard players reset @s sdp_ok"),
            ],
        }],
    }],
})

mc.cmd("reload")
print("  recargado")
