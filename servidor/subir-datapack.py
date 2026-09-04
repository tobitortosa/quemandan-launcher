# -*- coding: utf-8 -*-
"""
Sube el datapack entero al servidor y lo recarga.

    python servidor/subir-datapack.py

respaldar.py baja el datapack y este lo sube: son las dos mitades de lo mismo.
Antes de que existiera este script, los archivos del datapack se escribian a
mano con comandos sueltos y la unica copia viva estaba adentro del servidor.

Sube todo lo que haya en servidor/datapack/, asi que agregar una funcion nueva
no pide tocar ninguna lista.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import mc

LOCAL = os.path.join(AQUI, "datapack")
REMOTO = "/world/datapacks/sobrinosdepepe"

if __name__ == "__main__":
    subidos = 0
    for carpeta, _, archivos in os.walk(LOCAL):
        for nombre in sorted(archivos):
            ruta = os.path.join(carpeta, nombre)
            relativa = os.path.relpath(ruta, LOCAL).replace(os.sep, "/")
            mc.write(REMOTO + "/" + relativa, open(ruta, encoding="utf-8").read())
            print("  " + relativa)
            subidos += 1
    print("subidos %d archivos" % subidos)

    # /reload relee las funciones, los advancements, los predicados y los menus
    # de Inventory Menu. NO relee el cartel (eso es /styledsidebars reload) ni la
    # configuracion de EconomyCraft (esa pide reinicio).
    mc.cmd("reload")
    print("recargado")
