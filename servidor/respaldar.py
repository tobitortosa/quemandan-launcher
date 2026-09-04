# -*- coding: utf-8 -*-
"""
Baja del servidor la configuración que mantenemos nosotros y la deja en este
repositorio, para que exista una copia fuera de Minehost.

    python servidor/respaldar.py
"""
import os

import mc

AQUI = os.path.dirname(os.path.abspath(__file__))

ARCHIVOS = [
    # El menu de /comandos y los comandos propios.
    ("/config/melius-commands/commands/comandos.json", "comandos/comandos.json"),
    ("/config/melius-commands/commands/economia.json", "comandos/economia.json"),
    ("/config/melius-commands/commands/casa.json", "comandos/casa.json"),
    ("/config/melius-commands/commands/pvp.json", "comandos/pvp.json"),
    ("/config/melius-commands/commands/extras.json", "comandos/extras.json"),
    ("/config/melius-commands/commands/bounty.json", "comandos/bounty.json"),
    ("/config/melius-commands/commands/nightvision.json", "comandos/nightvision.json"),
    ("/config/melius-commands/commands/nv.json", "comandos/nv.json"),
    ("/config/melius-commands/commands/clearchat.json", "comandos/clearchat.json"),
    # Los modificadores cambian los permisos de comandos que no son nuestros.
    ("/config/melius-commands/modifiers/styledsidebars.json", "modificadores/styledsidebars.json"),
    ("/config/melius-commands/modifiers/clear.json", "modificadores/clear.json"),
    # El cartel de la derecha.
    ("/config/styled-sidebars/styles/default.json", "cartel/default.json"),
    # Las recompensas y la vision nocturna.
    ("/world/datapacks/sobrinosdepepe/pack.mcmeta", "datapack/pack.mcmeta"),
    ("/world/datapacks/sobrinosdepepe/data/minecraft/tags/function/tick.json",
     "datapack/data/minecraft/tags/function/tick.json"),
    ("/world/datapacks/sobrinosdepepe/data/sdp/advancement/kill.json",
     "datapack/data/sdp/advancement/kill.json"),
    ("/world/datapacks/sobrinosdepepe/data/sdp/predicate/tiene_nv.json",
     "datapack/data/sdp/predicate/tiene_nv.json"),
    ("/world/datapacks/sobrinosdepepe/data/sdp/function/tick.mcfunction",
     "datapack/data/sdp/function/tick.mcfunction"),
    ("/world/datapacks/sobrinosdepepe/data/sdp/function/on_kill.mcfunction",
     "datapack/data/sdp/function/on_kill.mcfunction"),
    ("/world/datapacks/sobrinosdepepe/data/sdp/function/cobrar.mcfunction",
     "datapack/data/sdp/function/cobrar.mcfunction"),
    ("/world/datapacks/sobrinosdepepe/data/sdp/function/pagar.mcfunction",
     "datapack/data/sdp/function/pagar.mcfunction"),
    ("/world/datapacks/sobrinosdepepe/data/sdp/function/nv.mcfunction",
     "datapack/data/sdp/function/nv.mcfunction"),
    ("/world/datapacks/sobrinosdepepe/data/sdp/function/nv_prender.mcfunction",
     "datapack/data/sdp/function/nv_prender.mcfunction"),
    ("/world/datapacks/sobrinosdepepe/data/sdp/function/nv_apagar.mcfunction",
     "datapack/data/sdp/function/nv_apagar.mcfunction"),
]

for remoto, local in ARCHIVOS:
    destino = os.path.join(AQUI, local.replace("/", os.sep))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8", newline="\n").write(mc.read(remoto))
    print("  " + local)

print("bajados %d archivos" % len(ARCHIVOS))
