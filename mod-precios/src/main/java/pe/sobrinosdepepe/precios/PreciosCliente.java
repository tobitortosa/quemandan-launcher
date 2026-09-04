package pe.sobrinosdepepe.precios;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback;
import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/**
 * Muestra en la descripcion de cada item cuanta plata paga el servidor por
 * venderlo, para no tener que abrir la tienda ni escribir /worth cada vez.
 *
 * Los precios viajan adentro del mod: son los mismos que tiene el servidor en
 * config/economycraft/prices.json. Si alguna vez cambian, hay que rearmar el
 * mod y publicarlo de nuevo, que es el precio de no depender del servidor para
 * dibujar un cartelito.
 */
public class PreciosCliente implements ClientModInitializer {
	private static final Logger LOG = LoggerFactory.getLogger("preciosdepepe");
	private static final Map<String, Integer> VENTA = new HashMap<>();

	@Override
	public void onInitializeClient() {
		cargarPrecios();

		ItemTooltipCallback.EVENT.register((pila, contexto, bandera, lineas) -> {
			var id = BuiltInRegistries.ITEM.getKey(pila.getItem());
			Integer unidad = VENTA.get(id.toString());
			if (unidad == null) return;

			lineas.add(linea(unidad, pila.getCount()));
		});
	}

	/** "Precio: $2" y, cuando hay varios, cuanto vale el monton entero. */
	private static Component linea(int unidad, int cantidad) {
		MutableComponent texto = Component.literal("Precio: ")
				.withStyle(ChatFormatting.DARK_GRAY)
				.append(Component.literal("$" + conPuntos(unidad)).withStyle(ChatFormatting.GOLD));

		if (cantidad > 1) {
			texto = texto
					.append(Component.literal("   x" + cantidad + " = ").withStyle(ChatFormatting.DARK_GRAY))
					.append(Component.literal("$" + conPuntos((long) unidad * cantidad))
							.withStyle(ChatFormatting.YELLOW));
		}

		return texto;
	}

	/** 12345 queda 12.345, igual que como muestra la plata el servidor. */
	private static String conPuntos(long valor) {
		String base = Long.toString(valor);
		StringBuilder salida = new StringBuilder();
		int corte = base.length() % 3;

		if (corte > 0) salida.append(base, 0, corte);

		for (int i = corte; i < base.length(); i += 3) {
			if (!salida.isEmpty()) salida.append('.');
			salida.append(base, i, i + 3);
		}

		return salida.toString();
	}

	private static void cargarPrecios() {
		try (InputStream entrada = PreciosCliente.class.getResourceAsStream("/precios.json")) {
			if (entrada == null) {
				LOG.error("El mod no trae precios.json adentro");
				return;
			}

			JsonObject json = JsonParser
					.parseReader(new InputStreamReader(entrada, StandardCharsets.UTF_8))
					.getAsJsonObject();

			for (Map.Entry<String, JsonElement> par : json.entrySet()) {
				VENTA.put(par.getKey(), par.getValue().getAsInt());
			}

			LOG.info("Cargados {} precios de venta", VENTA.size());
		} catch (Exception e) {
			LOG.error("No pude leer los precios", e);
		}
	}
}
