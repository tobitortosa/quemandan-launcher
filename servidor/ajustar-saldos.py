# -*- coding: utf-8 -*-
"""
Deja el saldo de cada jugador en proporción a las horas que jugó.

    python servidor/ajustar-saldos.py --ver     # solo muestra la tabla
    python servidor/ajustar-saldos.py           # la aplica

Se corrió una vez, el 2026-09-05, después de descubrir que el 100% de la plata
en circulación había salido del error de precio de los libros encantados: de los
2.132.824 que existían, 2.125.560 venían de ahí, y el 94% estaba en una sola
cuenta.

Deshacerlo item por item no era posible. Sacarle a Luquitas solo lo de libros lo
dejaba en -680.474, porque esa plata ya la había gastado (426.104 en compras) y
pasado (277.800 a Chichon). Así que en vez de reconstruir la historia se
reconstruye el resultado: cada uno tiene lo que habría juntado jugando esas
mismas horas.

Los 15.000 por hora están por DEBAJO de lo que rinde una hora de granja con los
precios de ahora (medido: entre 30 y 40 mil), así que nadie queda con menos de lo
que puede recuperar jugando.

Los shards no se tocan. Ya son la moneda de horas y kills, y nunca estuvieron
mal repartidos.

Las horas salen de `/world/players/stats/<uuid>.json`, que es el total de
siempre, y NO del objetivo `sdp_tiempo`, que arranca en cero cuando se crea el
objetivo y por eso solo cuenta desde que lo creamos.

Se usa `eco setmoney` y no se edita `balances.json`: el servidor tiene los saldos
en memoria y al guardar pisaría el archivo. Como `eco setmoney` devuelve éxito
pase lo que pase, la verificación es volver a leer el archivo.
"""
import json
import os
import sys
import time
import urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import mc

POR_HORA = 15000
PISO = 10000
RESPALDO = os.path.join(AQUI, "economia", "saldos-antes.json")


def miles(v):
    return "{:,}".format(int(v)).replace(",", ".")


def horas_jugadas(nombres):
    horas = {}
    listado = json.loads(mc.call(
        "/files/list?directory=" + urllib.parse.quote("/world/players/stats")))["data"]
    for e in listado:
        n = e["attributes"]["name"]
        if not n.endswith(".json"):
            continue
        stats = json.loads(mc.read("/world/players/stats/" + n)).get("stats", {})
        ticks = stats.get("minecraft:custom", {}).get("minecraft:play_time", 0)
        horas[nombres.get(n[:-5], n[:-5])] = ticks / 20 / 3600
    return horas


def armar_plan():
    nombres = {u["uuid"]: u["name"] for u in json.loads(mc.read("/usercache.json"))}
    saldos = json.loads(mc.read("/config/economycraft/data/balances.json"))
    horas = horas_jugadas(nombres)
    plan = []
    for uuid, viejo in saldos.items():
        nombre = nombres.get(uuid)
        h = horas.get(nombre, 0.0)
        nuevo = max(PISO, int(round(h * POR_HORA / 1000)) * 1000)
        plan.append((nombre, h, viejo, nuevo))
    plan.sort(key=lambda x: -x[1])
    return nombres, plan


def mostrar(plan):
    print("%-14s %8s %14s %14s" % ("jugador", "horas", "antes", "despues"))
    for nombre, h, viejo, nuevo in plan:
        print("%-14s %6.1f h %14s %14s" % (nombre, h, miles(viejo), miles(nuevo)))
    print("%-14s %8s %14s %14s" % ("TOTAL", "",
                                   miles(sum(p[2] for p in plan)),
                                   miles(sum(p[3] for p in plan))))


def aplicar(nombres, plan):
    os.makedirs(os.path.dirname(RESPALDO), exist_ok=True)
    json.dump({p[0]: p[2] for p in plan}, open(RESPALDO, "w", encoding="utf-8"), indent=2)
    print("guardados los saldos viejos en economia/saldos-antes.json")

    for nombre, _, _, nuevo in plan:
        mc.cmd("eco setmoney %s %d" % (nombre, nuevo))
    time.sleep(3)

    despues = json.loads(mc.read("/config/economycraft/data/balances.json"))
    print()
    print("verificación contra balances.json:")
    mal = 0
    for nombre, _, _, nuevo in plan:
        real = next((v for u, v in despues.items() if nombres.get(u) == nombre), None)
        if real != nuevo:
            mal += 1
        print("   %-14s esperado %-12s quedó %-12s %s"
              % (nombre, miles(nuevo), miles(real) if real is not None else "?",
                 "OK" if real == nuevo else "MAL"))
    return mal


if __name__ == "__main__":
    nombres, plan = armar_plan()
    mostrar(plan)
    if "--ver" in sys.argv:
        sys.exit(0)
    print()
    mal = aplicar(nombres, plan)
    print("todos correctos" if not mal else "%d saldos no quedaron como se pidió" % mal)
    sys.exit(1 if mal else 0)
