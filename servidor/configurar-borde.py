# -*- coding: utf-8 -*-
"""
Pone el borde del mundo, igual en las tres dimensiones.

    python servidor/configurar-borde.py

En 26.1 el borde es POR DIMENSIÓN. `WorldBorderCommand` trabaja siempre sobre
`source.getLevel().getWorldBorder()`, y cada nivel guarda el suyo aparte como
SavedData `minecraft:world_border` dentro de su propia carpeta `data/`. O sea que
un `/worldborder set` suelto en la consola configura solamente el overworld y en
el Nether se sigue caminando hasta el infinito. Por eso cada comando va con
`execute in <dimensión>`.

El tamaño sale de medir el mundo, no de una corazonada:

  - las regiones ya generadas llegan a 2.560 bloques en el overworld y a 1.024 en
    el Nether (el End todavía no existe);
  - la posición más lejana de un jugador es la de Titit0N, en z = -1.860;
  - la cama más lejana es la de Felix_1256, en (922, -1.593).

Con 4.000 de radio no queda afuera ni un chunk de los que ya existen, así que no
se pierde nada de lo construido, y todavía sobran 1.440 bloques de frontera nueva
para explorar en cada dirección.

El Nether lleva el mismo número y no la octava parte. Achicarlo a 500 de radio
para que coincidiera geográficamente con el overworld cortaría chunks que ya
están generados, que es justo lo que no queremos. Y no abre ningún agujero para
escaparse: el juego recorta el portal de vuelta contra el borde del overworld, así
que caminar 4.000 bloques de Nether no deja a nadie a 32.000 del spawn.
"""
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import estilo as e
import mc

# El spawn está en (48, 97, 0), o sea a 48 bloques del centro: la diferencia no se
# nota ni caminando, y los números redondos hacen que el borde se explique solo.
CENTRO_X, CENTRO_Z = 0, 0
TAMANO = 8000
RADIO = TAMANO // 2

# El aviso vanilla son 5 bloques, que es encima del borde. A 32 la pantalla se
# tiñe de rojo con tiempo de frenar.
#
# El tiempo va en TICKS y no en segundos, aunque el comando conteste en segundos:
# con 10 el servidor respondió "0.50 second(s)". El default de vanilla son 300,
# que son los 15 segundos de siempre.
AVISO_BLOQUES = 32
AVISO_TICKS = 200

DIMENSIONES = ["minecraft:overworld", "minecraft:the_nether", "minecraft:the_end"]


def t(texto, color=None, negrita=False):
    c = {"text": texto}
    if color:
        c["color"] = color
    if negrita:
        c["bold"] = True
    return c


def miles(n):
    return "{:,}".format(n).replace(",", ".")


def aplicar():
    for dim in DIMENSIONES:
        for comando in [
            "worldborder center %d %d" % (CENTRO_X, CENTRO_Z),
            "worldborder set %d" % TAMANO,
            "worldborder warning distance %d" % AVISO_BLOQUES,
            "worldborder warning time %d" % AVISO_TICKS,
        ]:
            mc.cmd("execute in %s run %s" % (dim, comando))
        print("  %s: %d bloques de lado" % (dim, TAMANO))


def anunciar():
    mensaje = ["",
               t(chr(10) + "  " + e.RAYA * 22 + chr(10), e.APAGADO),
               t("  " + e.ESTRELLA + " EL MUNDO AHORA TIENE BORDE " + e.ESTRELLA + chr(10),
                 e.MARCA, negrita=True),
               t("  " + miles(RADIO) + " bloques", e.ACENTO, negrita=True),
               t(" para cada lado desde el spawn." + chr(10), e.ETIQUETA),
               t("  Todo lo que construyeron queda adentro." + chr(10), e.ETIQUETA),
               t("  " + e.RAYA * 22 + chr(10), e.APAGADO)]
    mc.cmd("tellraw @a " + json.dumps(mensaje))


def verificar():
    """Lee el log para confirmar los tres bordes, en vez de confiar en que salió."""
    antes = len(mc.read("/logs/latest.log").splitlines())
    for dim in DIMENSIONES:
        mc.cmd("execute in %s run worldborder get" % dim)
    time.sleep(2)
    lineas = mc.read("/logs/latest.log").splitlines()[antes:]
    encontrados = [l for l in lineas if "world border" in l.lower()]
    for l in encontrados:
        print("  " + l.split("]: ")[-1])
    return len(encontrados)


if __name__ == "__main__":
    aplicar()
    anunciar()
    print("verificación:")
    if verificar() != len(DIMENSIONES):
        sys.exit("el servidor no confirmó el borde en las tres dimensiones")
    print("borde de %d bloques (%d de radio) en las %d dimensiones"
          % (TAMANO, RADIO, len(DIMENSIONES)))
