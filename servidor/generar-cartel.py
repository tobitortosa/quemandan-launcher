# -*- coding: utf-8 -*-
"""
Arma el cartel de la derecha y lo sube al servidor.

    python servidor/generar-cartel.py

Lo dibuja Styled Sidebars, que se recarga con /styledsidebars reload y NO con
/reload.

La forma es la del scoreboard clasico de DonutSMP: etiqueta a la izquierda,
valor a la derecha, un icono por fila y una linea vacia separando los bloques.
La alineacion NO se hace con espacios: cuando una linea es un array de dos
strings, Styled Sidebars manda la parte derecha como el "score" de la fila, que
el cliente dibuja pegado al borde. Con espacios quedaria desparejo porque la
fuente no es monoespaciada.

Tres limites que importan:
  - 14 lineas visibles. Si se pasa, el mod empieza a scrollear solo.
  - un array de UN elemento NO es una linea normal: el texto se va a la derecha.
    Para texto suelto va un string; para dos columnas, un array de dos.
  - los degrades no pueden envolver un placeholder (necesitan texto fijo), asi
    que el degrade va en el titulo y los valores llevan color plano.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import estilo as e
import mc


def fila(icono, color, etiqueta, valor):
    """Una fila: icono y etiqueta a la izquierda, valor pegado a la derecha."""
    return ["<%s>%s <gray>%s" % (color, icono, etiqueta), "<%s>%s" % (color, valor)]


cartel = {
    "config_name": "SobrinosDePepe",
    # Un segundo de refresco: los shards y la plata cambian de golpe y se quiere
    # ver el numero moverse cuando cobras una kill.
    "update_tick_time": 20,
    "page_change": 5,
    "title_change": 10,
    "scroll_speed": 1,
    "scroll_loop": True,
    "title": ["<b><gr:%s:%s>SOBRINOS DE PEPE</gr>" % (e.MARCA, e.MARCA_CLARA)],
    "lines": [
        "",
        # EconomyCraft ya devuelve la plata con el signo adelante y los puntos
        # de miles puestos, asi que aca no se agrega nada.
        fila(e.PESOS, e.PLATA, "Dinero", "%economycraft:balance_formatted%"),
        fila(e.SHARD, e.SHARDS, "Shards", "%player:objective Shards%"),
        "",
        fila(e.ESPADAS, e.KILLS, "Kills", "%player:statistic_raw player_kills%"),
        fila(e.CALAVERA, e.MUERTES, "Muertes", "%player:statistic_raw deaths%"),
        # NO usar %player:playtime%: en placeholder-api 3.0.0-beta.2 la version
        # sin argumento devuelve vacio (probado en el juego). Esta pasa por el
        # formateador de estadisticas del propio juego y sale como "13h 55m".
        fila(e.RELOJ, e.TIEMPO, "Jugado", "%player:statistic play_time%"),
        "",
        # "Tu cabeza" y no "Tu precio": el precio en la tienda es otra cosa.
        fila(e.CALAVERA, e.RECOMPENSA, "Tu cabeza", e.SHARD + "%player:objective Bounty%"),
        "",
        "<dark_gray>sobrinosdepepe.minehost.pro",
    ],
}

if __name__ == "__main__":
    assert len(cartel["lines"]) <= 14, "mas de 14 lineas activa el scroll solo"
    mc.write("/config/styled-sidebars/styles/default.json",
             json.dumps(cartel, indent=2, ensure_ascii=False))
    mc.cmd("styledsidebars reload")
    print("cartel actualizado")
    for l in cartel["lines"]:
        texto = l if isinstance(l, str) else "%-34s %s" % (l[0], l[1])
        print("   |" + texto.encode("ascii", "replace").decode())
