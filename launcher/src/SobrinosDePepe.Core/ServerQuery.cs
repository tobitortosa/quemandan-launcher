using System.Buffers.Binary;
using System.Net.Sockets;
using System.Text;

namespace SobrinosDePepe.Core;

public sealed record OnlinePlayers(bool Answered, List<string> Names)
{
    public static readonly OnlinePlayers NoAnswer = new(false, []);
}

/// <summary>
/// Pregunta al servidor quiénes están conectados en este momento.
///
/// El ping normal del listado devuelve cuántos hay, pero no siempre los nombres. El
/// protocolo de consulta sí devuelve la lista completa; hay que tenerlo habilitado en
/// el servidor con enable-query=true, que es el caso.
/// </summary>
public static class ServerQuery
{
    private const byte Magic1 = 0xFE;
    private const byte Magic2 = 0xFD;
    private const byte Handshake = 0x09;
    private const byte Stat = 0x00;

    public static async Task<OnlinePlayers> PlayersAsync(string address, int timeoutMs = 3000)
    {
        var (host, port) = await ServerStatus.ResolveAsync(address);

        try
        {
            using var client = new UdpClient();
            client.Client.SendTimeout = timeoutMs;
            client.Client.ReceiveTimeout = timeoutMs;
            client.Connect(host, port);

            using var cts = new CancellationTokenSource(timeoutMs);

            // Paso 1: pedir el desafío. El servidor contesta con un número que hay que
            // devolverle, para que nadie use el servidor como amplificador de tráfico.
            var session = 1 & 0x0F0F0F0F;
            await client.SendAsync(Frame(Handshake, session, []), cts.Token);

            var handshake = await client.ReceiveAsync(cts.Token);
            var challenge = ReadChallenge(handshake.Buffer);

            // Paso 2: pedir la estadística completa. Los cuatro ceros del final son los
            // que piden la versión larga, la que incluye la lista de jugadores.
            var payload = new byte[8];
            BinaryPrimitives.WriteInt32BigEndian(payload, challenge);
            await client.SendAsync(Frame(Stat, session, payload), cts.Token);

            var answer = await client.ReceiveAsync(cts.Token);
            return new OnlinePlayers(true, ReadPlayers(answer.Buffer));
        }
        catch (Exception ex) when (ex is SocketException or OperationCanceledException or IndexOutOfRangeException)
        {
            return OnlinePlayers.NoAnswer;
        }
    }

    private static byte[] Frame(byte type, int session, byte[] payload)
    {
        var frame = new byte[7 + payload.Length];
        frame[0] = Magic1;
        frame[1] = Magic2;
        frame[2] = type;
        BinaryPrimitives.WriteInt32BigEndian(frame.AsSpan(3), session);
        payload.CopyTo(frame, 7);
        return frame;
    }

    private static int ReadChallenge(byte[] buffer)
    {
        // Tipo (1) + sesión (4) + el número como texto terminado en cero.
        var end = Array.IndexOf(buffer, (byte)0, 5);
        if (end < 0) end = buffer.Length;
        var text = Encoding.ASCII.GetString(buffer, 5, end - 5).Trim();
        return int.Parse(text);
    }

    private static List<string> ReadPlayers(byte[] buffer)
    {
        // La respuesta larga trae dos secciones separadas por un marcador; la de los
        // jugadores viene después de "player_" y termina con dos ceros.
        var text = Encoding.UTF8.GetString(buffer);
        var marker = text.IndexOf("player_", StringComparison.Ordinal);
        if (marker < 0) return [];

        var start = marker + "player_".Length;

        // Después del marcador hay dos bytes en cero antes del primer nombre.
        while (start < text.Length && text[start] == '\0') start++;

        var names = new List<string>();
        var current = new StringBuilder();

        for (var i = start; i < text.Length; i++)
        {
            if (text[i] != '\0')
            {
                current.Append(text[i]);
                continue;
            }

            if (current.Length == 0) break;      // dos ceros seguidos: se terminó la lista
            names.Add(current.ToString());
            current.Clear();
        }

        if (current.Length > 0) names.Add(current.ToString());
        return names;
    }
}
