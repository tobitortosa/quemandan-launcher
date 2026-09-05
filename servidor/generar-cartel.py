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
    """Una fila: icono y etiqueta a la izquierda, valor pegado a la derecha.

    La etiqueta va en blanco y no en gris: sobre el fondo del cartel el gris casi
    no se lee. El icono y el valor mantienen su color, que es lo que distingue
    una fila de otra de un vistazo.
    """
    return ["<%s>%s <white>%s" % (color, icono, etiqueta), "<%s>%s" % (color, valor)]


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
    # Las cinco filas de datos son EXACTAMENTE las de DonutSMP, en su orden:
    # plata, shards, kills, muertes y tiempo jugado. No lleva el dominio (ellos
    # tampoco) ni la recompensa: el bounty sigue vivo, pero se mira con /bounty
    # y se avisa por chat cuando alguien pone una, que es como lo hacen alla.
    "lines": [
        # Sin linea en blanco despues del titulo: el titulo ya separa solo.
        # El formato corto, que es el que usa DonutSMP: $337k, $1.5k, $2.5M.
        # EconomyCraft lo devuelve YA con el signo adelante (formatMoneyShort
        # arranca con "$"), asi que esta fila va sin icono: ponerle el $ del lado
        # izquierdo lo dejaria dos veces. Es la unica de las cinco sin simbolo, y
        # es a proposito.
        #
        # Los otros dos placeholders de saldo tambien traen el signo, asi que no
        # hay forma de tener icono y numero corto a la vez: balance es el unico
        # que devuelve el numero pelado, pero sin separador de miles. Queda con el
        # $ dos veces, uno de icono y otro adentro del valor, y esta bien asi: la
        # fila se lee mejor con simbolo que con el hueco que quedaba antes.
        fila(e.PESOS, e.PLATA, "Dinero", "%economycraft:balance_short%"),
        fila(e.SHARD, e.SHARDS, "Shards", "%player:objective Shards%"),
        fila(e.ESPADAS, e.KILLS, "Kills", "%player:statistic_raw player_kills%"),
        fila(e.CALAVERA, e.MUERTES, "Muertes", "%player:statistic_raw deaths%"),
        # El placeholder de tiempo tiene dos trampas: sin argumento devuelve
        # VACIO (probado en el juego), y el formateador de estadisticas del juego
        # se pasa a dias con decimal a las 12 horas ("0.58 d"). Con el patron
        # explicito siempre sale en horas y minutos.
        fila(e.RELOJ, e.TIEMPO, "Jugado", "%player:playtime H'h' m'm'%"),
        "",
        # El cartel es el unico lugar que ve un jugador todo el tiempo, asi que
        # aca vive la pista de como se abre la interfaz. DonutSMP no tiene ningun
        # item que abra menus: todas sus GUIs se abren tipeando el comando, y el
        # indice de todas es /help. Aca ese indice es /ayuda.
        #
        # Va como instruccion y no como etiqueta. "para todo" obliga a deducir
        # que hay que escribirlo; "Escribi /ayuda" dice que hacer.
        "<white>Escribi <#00a6ff>/ayuda",
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
