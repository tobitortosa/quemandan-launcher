using System.Security.Cryptography;

namespace SobrinosDePepe.Core;

/// <summary>
/// Descarga archivos verificando el hash. Dos cosas que parecen "de más" y no lo son:
/// reintentar cuando se corta la red (con miles de archivos, que falle alguno es lo normal)
/// y comparar el hash (un archivo cortado no da error de descarga, da un crash de Java
/// que nadie puede diagnosticar).
/// </summary>
public sealed class HashedDownloader
{
    public const string UserAgent = "SobrinosDePepeLauncher/0.1 (tobias.tortosa@soution.com)";

    private readonly HttpClient _http;
    private readonly int _attempts;
    private readonly Uri? _backendUrl;
    private readonly string? _backendToken;

    /// <param name="backend">
    /// Dirección del backend y token de la sesión. Los archivos que el admin subió se
    /// descargan de ahí y hacen falta credenciales. El token se manda únicamente a ese
    /// dominio: a Mojang, a Fabric y a Modrinth no se les manda nada.
    /// </param>
    public HashedDownloader(HttpClient? http = null, int attempts = 3, (Uri Url, string Token)? backend = null)
    {
        _http = http ?? CreateHttpClient();
        _attempts = attempts;
        _backendUrl = backend?.Url;
        _backendToken = backend?.Token;
    }

    public static HttpClient CreateHttpClient()
    {
        var http = new HttpClient { Timeout = TimeSpan.FromMinutes(5) };
        http.DefaultRequestHeaders.UserAgent.ParseAdd(UserAgent);
        return http;
    }

    /// <summary>
    /// Deja el archivo en <paramref name="destination"/> con el hash esperado.
    /// Si ya está bien, no lo vuelve a bajar y devuelve false.
    /// </summary>
    public async Task<bool> EnsureFileAsync(
        string url,
        string destination,
        string? expectedSha1,
        string? expectedSha512,
        CancellationToken ct = default)
    {
        if (File.Exists(destination) && Matches(destination, expectedSha1, expectedSha512))
            return false;

        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        var temp = destination + ".part";

        Exception? last = null;
        for (var attempt = 1; attempt <= _attempts; attempt++)
        {
            try
            {
                using (var request = BuildRequest(url))
                using (var response = await _http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct))
                {
                    response.EnsureSuccessStatusCode();
                    await using var source = await response.Content.ReadAsStreamAsync(ct);
                    await using var target = File.Create(temp);
                    await source.CopyToAsync(target, ct);
                }

                if (!Matches(temp, expectedSha1, expectedSha512))
                    throw new InvalidDataException(
                        $"El archivo descargado no coincide con el hash esperado: {Path.GetFileName(destination)}");

                File.Move(temp, destination, overwrite: true);
                return true;
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                last = ex;
                TryDelete(temp);
                if (attempt < _attempts)
                    await Task.Delay(TimeSpan.FromSeconds(Math.Pow(2, attempt)), ct);
            }
        }

        throw new IOException(
            $"No se pudo descargar {Path.GetFileName(destination)} después de {_attempts} intentos.", last);
    }

    private HttpRequestMessage BuildRequest(string url)
    {
        var request = new HttpRequestMessage(HttpMethod.Get, url);

        if (_backendUrl is not null && _backendToken is not null &&
            Uri.TryCreate(url, UriKind.Absolute, out var target) &&
            Uri.Compare(target, _backendUrl, UriComponents.SchemeAndServer, UriFormat.Unescaped,
                StringComparison.OrdinalIgnoreCase) == 0)
        {
            request.Headers.Authorization =
                new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", _backendToken);
        }

        return request;
    }

    public static bool Matches(string path, string? expectedSha1, string? expectedSha512)
    {
        try
        {
            if (!string.IsNullOrEmpty(expectedSha1))
                return string.Equals(Sha1(path), expectedSha1, StringComparison.OrdinalIgnoreCase);
            if (!string.IsNullOrEmpty(expectedSha512))
                return string.Equals(Sha512(path), expectedSha512, StringComparison.OrdinalIgnoreCase);
            return true;
        }
        catch (IOException)
        {
            return false;
        }
    }

    public static string Sha1(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexStringLower(SHA1.HashData(stream));
    }

    public static string Sha512(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexStringLower(SHA512.HashData(stream));
    }

    private static void TryDelete(string path)
    {
        try { if (File.Exists(path)) File.Delete(path); } catch (IOException) { }
    }
}
