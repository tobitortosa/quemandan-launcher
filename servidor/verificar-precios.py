# -*- coding: utf-8 -*-
"""
Busca las formas de sacar plata infinita de la tienda.

    python servidor/verificar-precios.py                 # contra el servidor
    python servidor/verificar-precios.py <prices.json>   # contra un archivo

Correr esto DESPUES de cada cambio de precios.

La idea es una sola: **nada que se pueda fabricar comprando en la tienda puede
venderse por mas de lo que costo fabricarlo.** Y "fabricar" no es un paso: es
toda la cadena. La primera version de este chequeo costeaba una sola receta y
solo con precios directos de la tienda, y por eso no veia nada de esto:

  - el name tag son 1 papel + 1 pepita de metal. Ni el papel ni las pepitas se
    venden en la tienda, asi que la receta se salteaba entera. Pero el papel sale
    de la cana de azucar (2 cada uno) y las pepitas de un lingote de hierro (1,67
    cada una): $3,67 de insumos para un item que se vendia a $140.
  - la arena se compra a 2, se funde en vidrio, y 6 vidrios dan 16 paneles: $12
    de insumos por $16 de venta, 33% garantizado. Es la misma maquina que hundio
    la economia de DonutSMP con los slabs de madera.

Asi que el costo de cada item se calcula con un punto fijo:

    costo(x) = el menor entre
               lo que sale comprarlo en la tienda, y
               por cada receta que lo produce, la suma del costo de sus
               ingredientes dividida por cuantos salen

Se itera hasta que ningun costo baja mas. El combustible de los hornos no se
cuenta, que es el lado conservador: hace que el chequeo sea mas exigente y no
menos.
"""
import glob
import json
import os
import sys
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INFINITO = float("inf")

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


def salida_de(receta):
    """El item que produce la receta y cuantos salen."""
    resultado = receta.get("result", {})
    return resultado.get("id"), resultado.get("count", 1)


def costos(precios, recetas, etiquetas):
    """
    Cuanto sale conseguir cada item empezando desde la tienda, siguiendo todas
    las cadenas de crafteo. Punto fijo: se repite hasta que ningun costo baja.
    """
    costo = {k: (v["unit_buy"] if v["unit_buy"] > 0 else INFINITO)
             for k, v in precios.items()}

    # Las recetas se preparan una sola vez: aplanar etiquetas es lo caro.
    preparadas = []
    for _, receta in recetas:
        opciones = ingredientes(receta, etiquetas)
        salida, cantidad = salida_de(receta)
        if opciones and salida:
            preparadas.append((salida, cantidad, opciones))

    for _ in range(40):
        cambio = False
        for salida, cantidad, opciones in preparadas:
            total = 0.0
            for opcion in opciones:
                mejor = min((costo.get(i, INFINITO) for i in opcion), default=INFINITO)
                if mejor == INFINITO:
                    total = INFINITO
                    break
                total += mejor
            if total == INFINITO:
                continue
            candidato = total / cantidad
            if candidato < costo.get(salida, INFINITO) - 1e-9:
                costo[salida] = candidato
                cambio = True
        if not cambio:
            break
    return costo


def revisar(precios, recetas, etiquetas):
    """Devuelve las tres listas: ventas por encima de la compra, del costo, y bloques."""
    directas = [(k, v) for k, v in precios.items()
                if v["unit_buy"] > 0 and v["unit_sell"] >= v["unit_buy"]]

    costo = costos(precios, recetas, etiquetas)
    fabricables = []
    for item, v in precios.items():
        c = costo.get(item, INFINITO)
        if c < INFINITO and v["unit_sell"] > c:
            fabricables.append({
                "item": item, "venta": v["unit_sell"], "costo": c,
                "ganancia": v["unit_sell"] - c,
                "veces": v["unit_sell"] / c if c > 0 else INFINITO,
            })
    fabricables.sort(key=lambda x: -x["ganancia"])

    comprimidos = []
    for _, receta in recetas:
        if receta.get("type") != "minecraft:crafting_shaped":
            continue
        if receta.get("pattern") != ["###", "###", "###"]:
            continue
        claves = list(receta.get("key", {}).values())
        if len(claves) != 1 or not isinstance(claves[0], str) or claves[0].startswith("#"):
            continue
        unidad, bloque = claves[0], salida_de(receta)[0]
        if not bloque or unidad not in precios or bloque not in precios:
            continue
        vb, vu = precios[bloque]["unit_sell"], precios[unidad]["unit_sell"]
        if vb > 9 * vu:
            comprimidos.append((bloque, vb, unidad, vu, vb - 9 * vu))
    comprimidos.sort(key=lambda x: -x[4])

    return directas, fabricables, comprimidos


def informe(precios, recetas, etiquetas, tope=25):
    directas, fabricables, comprimidos = revisar(precios, recetas, etiquetas)

    print("1) items que se venden por mas de lo que se compran: %d" % len(directas))
    for k, v in directas[:tope]:
        print("     %-42s compra %-10d venta %d" % (k, v["unit_buy"], v["unit_sell"]))

    print("2) items que se venden por mas de lo que sale fabricarlos: %d" % len(fabricables))
    for c in fabricables[:tope]:
        print("     %-38s cuesta %-12.2f vende %-10d x%.1f"
              % (c["item"].replace("minecraft:", ""), c["costo"], c["venta"], c["veces"]))
    if len(fabricables) > tope:
        print("     ... y %d mas" % (len(fabricables) - tope))

    # Este tercero es un aviso y no una falla: comprimir para vender mejor no
    # crea plata de la nada, porque las unidades hay que conseguirlas igual. Solo
    # seria una maquina si la unidad se pudiera comprar, y eso lo caza el punto 2.
    print("3) aviso, bloques que valen mas que sus nueve unidades: %d" % len(comprimidos))
    for b, vb, u, vu, exceso in comprimidos[:tope]:
        print("     %-34s venta %-10d vs 9 x %-24s = %-10d exceso %d"
              % (b.replace("minecraft:", ""), vb, u.replace("minecraft:", ""), 9 * vu, exceso))

    return len(directas) + len(fabricables)


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
