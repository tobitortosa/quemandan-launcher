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
    """Devuelve (recetas, etiquetas, trueques) leidos del jar del juego."""
    if not JAR:
        print("No encuentro el jar del juego en la cache de Loom de mod-precios.")
        print("Corre una vez 'gradlew build' en mod-precios, o pasa el jar a mano.")
        sys.exit(1)
    z = zipfile.ZipFile(JAR[0])
    recetas = []
    etiquetas = {}
    trueques = []
    for nombre in z.namelist():
        if nombre.startswith("data/minecraft/recipe/") and nombre.endswith(".json"):
            recetas.append((nombre, json.loads(z.read(nombre))))
        elif nombre.startswith("data/minecraft/tags/item/") and nombre.endswith(".json"):
            clave = "#minecraft:" + nombre[len("data/minecraft/tags/item/"):-len(".json")]
            etiquetas[clave] = json.loads(z.read(nombre))
        # Los datapacks que vienen adentro del jar (trade_rebalance entre ellos)
        # estan apagados en este mundo: se ve en la lista Disabled del level.dat.
        elif ("data/minecraft/villager_trade/" in nombre and nombre.endswith(".json")
              and "datapacks" not in nombre):
            trueques.append((nombre.split("villager_trade/")[1][:-5], json.loads(z.read(nombre))))
    return recetas, etiquetas, trueques


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


def trueques_con_ganancia(precios, trueques):
    """Trueques de aldeano que dejan mas plata de la que costo lo que entregaste.

    Es el cuarto agujero, y el que de verdad rompio la economia: el punto fijo de
    los crafteos no lo veia porque un trueque no es una receta. Los aldeanos son
    la unica maquina del juego que convierte cosas renovables (zanahorias, papel,
    lana) en esmeraldas, y las esmeraldas en equipo. Si lo que te dan vale mas que
    lo que entregas, una sala de aldeanos imprime plata para siempre.

    Se valua todo a precio de VENTA, que es la plata que el jugador tendria si en
    vez de comerciar hubiera vendido los insumos en la tienda. Los trueques cuyo
    resultado no tiene precio (los libros encantados, las pociones) quedan afuera
    solos: no hay con que compararlos, que es exactamente por que no se venden.
    """
    # La tabla no tiene "minecraft:enchanted_book": tiene 121 entradas
    # enchanted_book_<encantamiento>_<nivel>. Si se buscara el id pelado el
    # trueque del librero quedaria afuera del chequeo, que es justo lo que paso.
    # Se usa el maximo de las variantes porque el jugador elige cual conseguir.
    variantes = {}
    for k, v in precios.items():
        if "_" in k and v["unit_sell"] > 0:
            raiz = k.rsplit("_", 1)[0].rsplit("_", 1)[0]
            variantes[raiz] = max(variantes.get(raiz, 0), v["unit_sell"])

    def valor(item, cantidad):
        p = precios.get(item)
        if p and p["unit_sell"] > 0:
            return p["unit_sell"] * cantidad
        if item in variantes:
            return variantes[item] * cantidad
        return None

    ganadores = []
    for nombre, t in trueques:
        da, quiere = t.get("gives"), t.get("wants")
        if not da or not quiere or "id" not in da:
            continue
        pide = quiere if isinstance(quiere, list) else [quiere]
        if "additional_wants" in t:
            pide = pide + [t["additional_wants"]]
        entra = 0
        for q in pide:
            v = valor(q.get("id"), int(q.get("count", 1))) if "id" in q else None
            if v is None:
                entra = None
                break
            entra += v
        sale = valor(da["id"], int(da.get("count", 1)))
        if entra is None or sale is None or sale <= entra:
            continue
        # max_uses es cuantas veces se puede hacer antes de que el aldeano se
        # quede sin stock; repone dos veces por dia si duerme y trabaja.
        usos = int(t.get("max_uses", 12))
        ganadores.append({
            "trueque": nombre, "entrega": entra, "recibe": sale,
            "ganancia": sale - entra, "por_dia": (sale - entra) * usos * 2,
        })
    ganadores.sort(key=lambda x: -x["por_dia"])
    return ganadores


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


# Un trueque que deja ganancia no es de por si una maquina: los aldeanos hay que
# criarlos, subirlos de nivel y darles de comer, y el stock se agota. Lo que no
# puede pasar es que UN aldeano solo rinda como un dia entero de granja, que
# medido en este servidor son unos 170.000 por dia.
TOPE_TRUEQUE_POR_DIA = 25000


def informe(precios, recetas, etiquetas, trueques, tope=25):
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

    ganadores = trueques_con_ganancia(precios, trueques)
    graves = [g for g in ganadores if g["por_dia"] > TOPE_TRUEQUE_POR_DIA]
    print("4) trueques de aldeano que dejan ganancia: %d, y %d pasan los %d por dia"
          % (len(ganadores), len(graves), TOPE_TRUEQUE_POR_DIA))
    for g in ganadores[:tope]:
        print("     %-46s entregas %-8d recibis %-8d gana %-8d %d/dia"
              % (g["trueque"], g["entrega"], g["recibe"], g["ganancia"], g["por_dia"]))

    return len(directas) + len(fabricables) + len(graves)


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else None
    if ruta:
        precios = json.load(open(ruta, encoding="utf-8"))
    else:
        sys.path.insert(0, AQUI)
        import mc
        precios = json.loads(mc.read("/config/economycraft/prices.json"))
    precios = {k: v for k, v in precios.items() if not k.startswith("_")}
    recetas, etiquetas, trueques = cargar_juego()
    print("%d precios, %d recetas, %d etiquetas de items, %d trueques"
          % (len(precios), len(recetas), len(etiquetas), len(trueques)))
    fallas = informe(precios, recetas, etiquetas, trueques)
    print("total de fallas: %d" % fallas)
    sys.exit(1 if fallas else 0)
