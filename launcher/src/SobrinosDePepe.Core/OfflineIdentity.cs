using System.Security.Cryptography;

namespace SobrinosDePepe.Core;

/// <summary>
/// El servidor corre en online-mode=false, así que ignora el UUID que manda el cliente
/// y calcula el suyo: UUID versión 3 del MD5 de "OfflinePlayer:&lt;nombre&gt;".
/// El inventario y el progreso de cada jugador están guardados bajo ese UUID, y es
/// sensible a mayúsculas: "PEPE" y "Pepe" son dos jugadores distintos.
/// Mandamos exactamente el mismo UUID que calcularía el servidor para que todo coincida.
/// </summary>
public static class OfflineIdentity
{
    public static Guid UuidFor(string username)
    {
        var hash = MD5.HashData(System.Text.Encoding.UTF8.GetBytes("OfflinePlayer:" + username));

        // Versión 3 y variante RFC 4122.
        hash[6] = (byte)((hash[6] & 0x0F) | 0x30);
        hash[8] = (byte)((hash[8] & 0x3F) | 0x80);

        // Los primeros tres campos de un Guid de .NET son little-endian; el UUID es big-endian.
        Array.Reverse(hash, 0, 4);
        Array.Reverse(hash, 4, 2);
        Array.Reverse(hash, 6, 2);

        return new Guid(hash);
    }

    /// <summary>Con guiones, como lo escribe whitelist.json.</summary>
    public static string Dashed(string username) => UuidFor(username).ToString("D");

    /// <summary>Sin guiones, como lo espera el argumento --uuid del juego.</summary>
    public static string Plain(string username) => UuidFor(username).ToString("N");
}
