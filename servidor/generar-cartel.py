# -*- coding: utf-8 -*-
"""
Arma el cartel de la derecha y lo sube al servidor.

    python servidor/generar-cartel.py

Lo dibuja Styled Sidebars, que se recarga con /styledsidebars reload y NO con
/reload. Los valores salen de placeholders: la plata la pone EconomyCraft (que
ya la trae con el signo adelante, así que no hay que agregarlo), las kills y las
muertes salen de las estadísticas del juego (así arrancan con el historial real
de cada uno) y la recompensa sale del scoreboard que usa /bounty.
"""
import json

import mc

FLECHA = chr(0xbb)


def linea(etiqueta, valor, ancho=10):
    relleno = " " * max(1, ancho - len(etiqueta))
    return "<gray>%s <white>%s%s%s" % (FLECHA, etiqueta, relleno, valor)


estilo = {
    "config_name": "SobrinosDePepe",
    "update_tick_time": 20,
    "page_change": 5,
    "title_change": 10,
    "scroll_speed": 1,
    "scroll_loop": True,
    "title": ["<b><gold>SOBRINOS DE PEPE"],
    "lines": [
        "",
        linea("Dinero", "<green><b>%economycraft:balance_formatted%"),
        linea("Kills", "<red>%player:statistic_raw player_kills%"),
        linea("Muertes", "<#ff8080>%player:statistic_raw deaths%"),
        "",
        # "Tu cabeza" y no "Tu precio": el precio en la tienda es otra cosa.
        linea("Tu cabeza", "<gold>$%player:objective Bounty%"),
        "",
    ],
}

mc.write("/config/styled-sidebars/styles/default.json", json.dumps(estilo, indent=2, ensure_ascii=False))
mc.cmd("styledsidebars reload")
print("cartel actualizado")
for l in estilo["lines"]:
    print("   |" + l.encode("ascii", "replace").decode())
