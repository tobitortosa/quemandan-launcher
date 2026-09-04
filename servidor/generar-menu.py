# -*- coding: utf-8 -*-
"""
Arma el menu de /comandos y lo sube al servidor.

    python servidor/generar-menu.py

Melius Commands ejecuta un tellraw por comando, asi que el menu se escribe como
componentes de texto. Los comandos que no necesitan datos se ejecutan al clickear
y los que si los necesitan se escriben en el chat para que el jugador complete.

Los simbolos se escriben con chr() y el JSON sale de json.dumps a proposito: una
barra invertida suelta en este archivo termina siendo un salto de linea real
adentro del comando y lo parte al medio.
"""
import json

import mc

GOLD, YEL, AQUA, GRAY, DGRAY, GREEN, RED, WHITE = (
    "gold", "yellow", "aqua", "gray", "dark_gray", "green", "red", "white")

RAYA = chr(0x25ac)      # el borde de los titulos
PUNTO = chr(0x2022)     # la vineta de cada comando
FLECHA = chr(0xbb)      # separa el comando de su explicacion
CUADRO = chr(0x25aa)    # la vineta de las advertencias
VOLVER = chr(0xab)      # la flecha de "volver"
ESPADAS = chr(0x2694)
CALAVERA = chr(0x2620)
LUNA = chr(0x263d)


def t(texto, color=None, bold=False, run=None, suggest=None, hover=None):
    c = {"text": texto}
    if color: c["color"] = color
    if bold: c["bold"] = True
    if run: c["click_event"] = {"action": "run_command", "command": run}
    if suggest: c["click_event"] = {"action": "suggest_command", "command": suggest}
    if hover: c["hover_event"] = {"action": "show_text", "value": hover}
    return c


def borde(titulo):
    return [t(chr(10) + RAYA * 8 + " " + titulo + " " + RAYA * 8 + chr(10) + chr(10), GOLD, bold=True)]


def fila(comando, desc, ancho=17, run=None, suggest=None, hover=None):
    relleno = " " * max(1, ancho - len(comando))
    return [
        t(" " + PUNTO + " ", DGRAY),
        t(comando, AQUA, run=run, suggest=suggest,
          hover=hover or ("Clickea para ejecutar " + comando if run else "Clickea para escribirlo en el chat")),
        t(relleno + FLECHA + "  ", DGRAY),
        t(desc + chr(10), GRAY),
    ]


def volver():
    return [
        t(chr(10) + " "),
        t(VOLVER + " VOLVER AL MENU", YEL, bold=True, run="/comandos", hover="Volver a las categorias"),
        t(chr(10) + RAYA * 30, GOLD, bold=True),
    ]


def guardar(cid, partes):
    doc = {"id": cid, "executes": [{"command": "tellraw @s " + json.dumps([""] + partes)}]}
    mc.write("/config/melius-commands/commands/%s.json" % cid,
             json.dumps(doc, indent=2, ensure_ascii=False))
    print("  escrito %s.json" % cid)


# ---------------------------------------------------------------- menu principal
def boton(icono, nombre, desc, comando):
    return [
        t("  " + icono + " ", WHITE),
        t("[ " + nombre + " ]", GREEN, bold=True, run=comando,
          hover="Clickea para ver los comandos de " + nombre.lower()),
        t(" " * max(1, 14 - len(nombre)) + desc + chr(10), GRAY),
    ]


menu = borde("SOBRINOS DE PEPE")
menu += [t("  Clickea una categoria:" + chr(10) * 2, WHITE)]
menu += boton(chr(0x1F4B0), "ECONOMIA", "Plata, tienda y subastas", "/economia")
menu += boton(chr(0x1F3E0), "CASA", "Homes, viajes y spawn", "/casa")
menu += boton(ESPADAS, "PVP", "Peleas, ranking y riesgo", "/pvp")
menu += boton(chr(0x1F5FA), "EXTRAS", "Mapa, voz, skin y mas", "/extras")
menu += [t(chr(10) + RAYA * 30, GOLD, bold=True)]
guardar("comandos", menu)

# ---------------------------------------------------------------------- economia
eco = borde(chr(0x1F4B0) + " ECONOMIA")
eco += fila("/bal", "Ver cuanta plata tenes", run="/bal")
eco += fila("/bal top", "El ranking de los mas ricos", run="/bal top")
eco += fila("/daily", "Tu regalo diario de $100", run="/daily")
eco += fila("/shop", "Tienda del servidor: comprar", run="/shop")
eco += fila("/sell", "Vender lo que traes encima", run="/sell")
eco += fila("/worth", "Cuanto vale lo que tenes en la mano", run="/worth")
eco += fila("/pay <jug> <$>", "Pagarle a otro jugador", suggest="/pay ")
eco += fila("/ah", "Subastas: vender a otros jugadores", run="/ah")
eco += fila("/orders", "Ordenes de compra: pedir algo", run="/orders")
eco += fila("/transactions", "Tu historial de plata", run="/transactions")
eco += volver()
guardar("economia", eco)

# -------------------------------------------------------------------------- casa
casa = borde(chr(0x1F3E0) + " CASA Y VIAJES")
casa += fila("/home set casa", "Guardar donde estas parado", suggest="/home set casa")
casa += fila("/home casa", "Viajar a tu casa", run="/home casa")
casa += fila("/spawn", "Volver al spawn del servidor", run="/spawn")
casa += fila("/rtp", "Tirarte a un lugar random del mapa", run="/rtp")
casa += fila("/warp <lugar>", "Los lugares del servidor", suggest="/warp ")
casa += fila("/tpa <jugador>", "Pedirle ir hasta el a alguien", suggest="/tpa ")
casa += fila("/tpaccept", "Aceptar que alguien venga", run="/tpaccept")
casa += fila("/tpdeny", "Rechazar el pedido", run="/tpdeny")
casa += fila("/back", "Volver a tu ultimo teletransporte", run="/back")
casa += fila("/top", "Subir a la superficie", run="/top")
casa += volver()
guardar("casa", casa)

# --------------------------------------------------------------------------- pvp
pvp = borde(CALAVERA + " PVP Y RECOMPENSAS")
pvp += [
    t("   El PvP esta activo en ", GRAY), t("TODO el mundo" + chr(10) * 2, RED, bold=True),
    t("   " + CUADRO + "  ", RED), t("Si te matan, ", GRAY), t("perdes lo que llevas" + chr(10), WHITE),
    t("   " + CUADRO + "  ", RED), t("Las bases ", GRAY), t("NO estan protegidas" + chr(10), WHITE),
    t("   " + CUADRO + "  ", RED), t("Cualquiera puede entrar a tu casa" + chr(10) * 2, GRAY),
    t("   " + CALAVERA + " PONER PRECIO A UNA CABEZA" + chr(10) * 2, GOLD, bold=True),
]
pvp += fila("/bounty", "Ver la lista de buscados", ancho=22, run="/bounty")
pvp += fila("/bounty <jugador> <$>", "Poner precio a alguien", ancho=22,
            suggest="/bounty ", hover="La plata sale de tu bolsillo")
pvp += [
    t(chr(10) + "   La plata sale de ", GRAY), t("tu bolsillo", WHITE),
    t(" y se la lleva" + chr(10) + "   quien lo mate. Varios pueden sumar a la" + chr(10) +
      "   misma cabeza: la recompensa se acumula." + chr(10), GRAY),
]
pvp += volver()
guardar("pvp", pvp)

# ------------------------------------------------------------------------ extras
ext = borde(chr(0x1F5FA) + " EXTRAS")
ext += fila("/nv", "Ver de noche en las cuevas", run="/nv",
            hover="Se prende y se apaga con el mismo comando")
ext += fila("/waypoint", "Marcar un punto en tu mapa", suggest="/waypoint ")
ext += fila("/skin set <nombre>", "Ponerte la skin de otra cuenta", suggest="/skin set ")
ext += fila("/nickname <apodo>", "Tu apodo en el chat", suggest="/nickname ")
ext += fila("/afk", "Avisar que te vas un rato", run="/afk")
ext += fila("/enderchest", "Tu cofre de ender donde estes", run="/enderchest")
ext += fila("/workbench", "Mesa de crafteo portatil", run="/workbench")
ext += fila("/msg <jug>", "Mensaje privado a alguien", suggest="/msg ")
ext += fila("/voicechat", "Ajustes del chat de voz", run="/voicechat")
ext += volver()
guardar("extras", ext)

mc.cmd("reload")
print("  recargado")
