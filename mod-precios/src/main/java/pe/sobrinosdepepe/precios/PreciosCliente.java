package pe.sobrinosdepepe.precios;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
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
			if (soloEspacios(lineas)) {
				lineas.clear();
				return;
			}

			if (esBoton(pila) || !esTuyo(pila)) return;

			var id = BuiltInRegistries.ITEM.getKey(pila.getItem());
			Integer unidad = VENTA.get(id.toString());
			if (unidad == null) return;

			lineas.add(linea(unidad, pila.getCount()));
		});
	}

	/**
	 * Los botones de los menus de cofre del servidor no son objetos: son iconos.
	 * Ponerle "Precio: $180" al lingote de oro que abre ECONOMIA no informa nada
	 * y ensucia un menu que ya tiene su propio texto.
	 *
	 * La marca la pone el servidor en custom_data, y tiene que ser ese componente
	 * y no otro. La primera version miraba tooltip_display, que parecia la marca
	 * natural porque los items de menu lo llevan para esconder el dano de ataque.
	 * Pero tooltip_display esta en COMMON_ITEM_COMPONENTS: TODOS los items lo
	 * traen por defecto, asi que el chequeo daba verdadero siempre y desaparecio
	 * el precio del inventario entero. custom_data no esta en esa lista, o sea
	 * que un item normal no lo tiene nunca.
	 */
	private static boolean esBoton(ItemStack pila) {
		CustomData datos = pila.get(DataComponents.CUSTOM_DATA);
		return datos != null && datos.copyTag().contains("sdp");
	}

	/**
	 * Un cartel cuyo texto es todo espacios se borra, asi no queda el cuadrito
	 * negro vacio flotando.
	 *
	 * Es para el relleno de los menus de EconomyCraft: su MenuUiSupport.filler()
	 * es un vidrio gris con custom_name de un solo espacio y sin tooltip_display,
	 * asi que el juego le dibuja una caja con una linea en blanco adentro. Antes
	 * no se notaba porque este mod le metia el precio del vidrio adentro.
	 *
	 * Nuestros propios menus no pasan por aca: su relleno lleva tooltip_display
	 * con hide_tooltip, y con eso ItemStack.getTooltipLines devuelve la lista
	 * vacia directamente. Y una lista vacia no dibuja nada, porque
	 * setTooltipForNextFrameInternal arranca con "if (!lines.isEmpty())".
	 *
	 * Borrar es seguro: solo saca carteles que iban a verse vacios igual. Un item
	 * de verdad siempre tiene el nombre, que no es blanco.
	 */
	private static boolean soloEspacios(java.util.List<Component> lineas) {
		if (lineas.isEmpty()) return false;

		for (Component linea : lineas) {
			if (!linea.getString().isBlank()) return false;
		}

		return true;
	}

	/**
	 * El precio se muestra solo en lo que el jugador tiene EN LA MANO O EN EL
	 * INVENTARIO, y no en cualquier item que aparezca en una pantalla.
	 *
	 * La marca de custom_data alcanza para nuestros menus, pero no para los de
	 * EconomyCraft: sus botones salen de MenuUiSupport.button() y sus items de un
	 * new ItemStack() pelado, o sea que no traen ninguna senal que se pueda leer
	 * desde afuera. Adentro del /shop nuestra linea encima era ademas repetida,
	 * porque EconomyCraft ya escribe ahi cuanto sale y cuanto paga.
	 *
	 * Se compara por IDENTIDAD y no por contenido. Los slots del inventario del
	 * jugador devuelven el mismo objeto ItemStack que tiene el inventario, asi que
	 * la comparacion es exacta; los items que dibuja un menu son copias aparte y
	 * nunca coinciden. Compararlos por contenido daria falsos positivos con
	 * cualquier item de la tienda que el jugador tambien tenga.
	 *
	 * Lo que se pierde: los items adentro de un cofre abierto dejan de mostrar el
	 * precio, porque no estan en el inventario. Del lado del cliente un cofre y
	 * el menu de una tienda son los dos un ChestMenu y no hay forma de
	 * distinguirlos.
	 */
	private static boolean esTuyo(ItemStack pila) {
		LocalPlayer jugador = Minecraft.getInstance().player;
		if (jugador == null) return false;

		Inventory inventario = jugador.getInventory();
		for (int i = 0; i < inventario.getContainerSize(); i++) {
			if (inventario.getItem(i) == pila) return true;
		}

		return false;
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
