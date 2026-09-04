# Si murio alguien que tenia precio en su cabeza, se le paga a quien lo mato.
execute as @a[scores={sdp_death=1..,Bounty=1..}] run function sdp:cobrar

# El contador de muertes se reinicia todos los ticks: solo interesa este.
scoreboard players reset * sdp_death
scoreboard players reset * sdp_killer

# Deja el precio en cero a quien no tenga, para que el cartel muestre algo.
scoreboard players add @a Bounty 0
