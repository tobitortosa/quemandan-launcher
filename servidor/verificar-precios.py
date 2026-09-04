# -*- coding: utf-8 -*-
"""
Busca las tres formas de sacar plata infinita de la tienda.

    python servidor/verificar-precios.py

Correr esto DESPUES de cada cambio de precios. Las tres fallas que busca:

1. Un item que se venda por mas de lo que se compra. Es la mas obvia y la unica
   que ya estaba controlada.
2. Una receta cuyos ingredientes se puedan comprar todos en la tienda y cuyo
   resultado se venda por mas que la suma de los ingredientes. Es la que hundio
   la economia de DonutSMP: alla un log de madera cuesta $72 y crafteado en 8
   slabs vale $96 en la venta, o sea 30% garantizado sin riesgo.
3. Una receta reversible (el bloque y sus nueve unidades) donde el bloque valga
   mas de nueve veces la unidad.

Las recetas salen del jar del juego, no de una lista escrita a mano: si Mojang
agrega una receta nueva, el chequeo la ve sola. El jar sale de la cache de Loom
del mod de precios, que ya tiene la version exacta del servidor.
"""
import glob
import json
import os
import sys
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

JAR = glob.glob(os.path.join(
    RAIZ, "mod-precios", ".gradle", "loom-cache", "minecraftMaven", "net", "minecraft",
    "**", "*-26.1.jar"), recursive=True)


def cargar_juego():
    """Devuelve (recetas, etiquetas) leidas del jar del juego."""
    if not JAR:
        print("No encuentro el jar del juego en la cache de Loom de mod-precios.")
        print("Corre una vez 'gradlew build' en mod-precios, o pasa el jar a mano.")
        sys.exit(1)
    z = zipfile.ZipFile(JAR[0])
    recetas = []
    etiquetas = {}
    for nombre in z.namelist():
        if nombre.startswith("data/minecraft/recipe/") and nombre.endswith(".json"):
            recetas.append((nombre, json.loads(z.read(nombre))))
        elif nombre.startswith("data/minecraft/tags/item/") and nombre.endswith(".json"):
            clave = "#minecraft:" + nombre[len("data/minecraft/tags/item/"):-len(".json")]
            etiquetas[clave] = json.loads(z.read(nombre))
    return recetas, etiquetas


def resolver(ingrediente, etiquetas, visto=None):
    """Una etiqueta puede contener otras etiquetas, asi que se aplana en items."""
    if visto is None:
        visto = set()
    if not ingrediente.startswith("#"):
        return [ingrediente]
    if ingrediente in visto or ingrediente not in etiquetas:
        return []
    visto.add(ingrediente)
    salida = []
    for v in etiquetas[ingrediente].get("values", []):
        v = v["id"] if isinstance(v, dict) else v
        salida += resolver(v, etiquetas, visto)
    return salida


def ingredientes(receta, etiquetas):
    """Lista plana de ingredientes, cada uno como las opciones que lo satisfacen."""
    tipo = receta.get("type", "")
    opciones = []
    if tipo == "minecraft:crafting_shaped":
        claves = receta.get("key", {})
        for fila in receta.get("pattern", []):
            for c in fila:
                if c != " " and c in claves:
                    v = claves[c]
                    v = v if isinstance(v, list) else [v]
                    opciones.append([x for i in v for x in resolver(i, etiquetas)])
    elif tipo in ("minecraft:crafting_shapeless", "minecraft:crafting_transmute"):
        for i in receta.get("ingredients", []):
            i = i if isinstance(i, list) else [i]
            opciones.append([x for v in i for x in resolver(v, etiquetas)])
        for campo in ("input", "material"):
            if campo in receta:
                v = receta[campo]
                v = v if isinstance(v, list) else [v]
                opciones.append([x for i in v for x in resolver(i, etiquetas)])
    elif tipo in ("minecraft:smelting", "minecraft:blasting", "minecraft:smoking",
                  "minecraft:campfire_cooking", "minecraft:stonecutting"):
        v = receta.get("ingredient", [])
        v = v if isinstance(v, list) else [v]
        opciones.append([x for i in v for x in resolver(i, etiquetas)])
    elif tipo == "minecraft:smithing_transform":
        for campo in ("base", "addition", "template"):
            if campo in receta:
                v = receta[campo]
                v = v if isinstance(v, list) else [v]
                opciones.append([x for i in v for x in resolver(i, etiquetas)])
    else:
        return None      # recetas especiales: no se pueden costear
    return [o for o in opciones if o]


def revisar(precios, recetas, etiquetas):
    """Devuelve las tres listas de fallas."""
    def compra(item):
        p = precios.get(item)
        return p["unit_buy"] if p and p["unit_buy"] > 0 else None

    def venta(item):
        p = precios.get(item)
        return p["unit_sell"] if p else 0

    # 1. venta >= compra en el mismo item
    directas = [(k, v) for k, v in precios.items()
                if v["unit_buy"] > 0 and v["unit_sell"] >= v["unit_buy"]]

    # 2. craftear desde la tienda y vender el resultado
    crafteo = []
    for nombre, receta in recetas:
        opciones = ingredientes(receta, etiquetas)
        if not opciones:
            continue
        resultado = receta.get("result", {})
        salida = resultado.get("id")
        if not salida:
            continue
        cantidad = resultado.get("count", 1)
        # El ingrediente se compra por la opcion mas barata que ofrezca la tienda.
        costo = 0
        for opcion in opciones:
            precios_opcion = [compra(i) for i in opcion]
            precios_opcion = [p for p in precios_opcion if p is not None]
            if not precios_opcion:
                costo = None       # este ingrediente no se vende: no hay maquina
                break
            costo += min(precios_opcion)
        if costo is None:
            continue
        ingreso = venta(salida) * cantidad
        if ingreso > costo:
            crafteo.append({
                "receta": nombre.split("/")[-1][:-5],
                "salida": salida,
                "cantidad": cantidad,
                "ingreso": ingreso,
                "costo": costo,
                "ganancia": ingreso - costo,
            })
    crafteo.sort(key=lambda x: -x["ganancia"])

    # 3. bloque comprimido que valga mas que sus nueve unidades
    comprimidos = []
    for nombre, receta in recetas:
        if receta.get("type") != "minecraft:crafting_shaped":
            continue
        patron = receta.get("pattern", [])
        if patron != ["###", "###", "###"]:
            continue
        claves = list(receta.get("key", {}).values())
        if len(claves) != 1 or not isinstance(claves[0], str) or claves[0].startswith("#"):
            continue
        unidad, bloque = claves[0], receta.get("result", {}).get("id")
        if not bloque or unidad not in precios or bloque not in precios:
            continue
        if venta(bloque) > 9 * venta(unidad):
            comprimidos.append((bloque, venta(bloque), unidad, venta(unidad),
                                venta(bloque) - 9 * venta(unidad)))
    comprimidos.sort(key=lambda x: -x[4])

    return directas, crafteo, comprimidos


def informe(precios, recetas, etiquetas, tope=25):
    directas, crafteo, comprimidos = revisar(precios, recetas, etiquetas)

    print("1) items que se venden por mas de lo que se compran: %d" % len(directas))
    for k, v in directas[:tope]:
        print("     %-42s compra %-10d venta %d" % (k, v["unit_buy"], v["unit_sell"]))

    print("2) recetas rentables comprando todo en la tienda: %d" % len(crafteo))
    for c in crafteo[:tope]:
        print("     %-34s x%-3d  cuesta %-10d rinde %-10d gana %d"
              % (c["salida"].replace("minecraft:", ""), c["cantidad"],
                 c["costo"], c["ingreso"], c["ganancia"]))
    if len(crafteo) > tope:
        print("     ... y %d mas" % (len(crafteo) - tope))

    # Este tercero es un aviso y no una falla: comprimir para vender mejor no
    # crea plata de la nada, porque las unidades hay que conseguirlas igual. Solo
    # seria una maquina si la unidad se pudiera comprar, y eso lo caza el punto 2.
    print("3) aviso, bloques que valen mas que sus nueve unidades: %d" % len(comprimidos))
    for b, vb, u, vu, exceso in comprimidos[:tope]:
        print("     %-34s venta %-10d vs 9 x %-24s = %-10d exceso %d"
              % (b.replace("minecraft:", ""), vb, u.replace("minecraft:", ""), 9 * vu, exceso))

    return len(directas) + len(crafteo)


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else None
    if ruta:
        precios = json.load(open(ruta, encoding="utf-8"))
    else:
        sys.path.insert(0, AQUI)
        import mc
        precios = json.loads(mc.read("/config/economycraft/prices.json"))
    precios = {k: v for k, v in precios.items() if not k.startswith("_")}
    recetas, etiquetas = cargar_juego()
    print("%d precios, %d recetas, %d etiquetas de items" % (len(precios), len(recetas), len(etiquetas)))
    fallas = informe(precios, recetas, etiquetas)
    print("total de fallas: %d" % fallas)
    sys.exit(1 if fallas else 0)
