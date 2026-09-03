using System.Text.Json;

namespace SobrinosDePepe.App;

/// <summary>
/// La dirección del backend. Viene compilada, y se puede cambiar sin recompilar
/// poniendo un archivo launcher.json al lado del ejecutable. Sirve para probar
/// contra el backend local sin tocar el código.
/// </summary>
public static class AppConfig
{
    public const string DefaultApiUrl = "https://sobrinosdepepe.vercel.app";

    public static Uri ApiUrl { get; } = Resolve();

    private static Uri Resolve()
    {
        var fromEnvironment = Environment.GetEnvironmentVariable("QUEMANDAN_API");
        if (!string.IsNullOrWhiteSpace(fromEnvironment) &&
            Uri.TryCreate(fromEnvironment, UriKind.Absolute, out var envUri))
            return envUri;

        var file = Path.Combine(AppContext.BaseDirectory, "launcher.json");
        if (File.Exists(file))
        {
            try
            {
                using var document = JsonDocument.Parse(File.ReadAllText(file));
                if (document.RootElement.TryGetProperty("apiUrl", out var value) &&
                    Uri.TryCreate(value.GetString(), UriKind.Absolute, out var fileUri))
                    return fileUri;
            }
            catch (Exception ex) when (ex is IOException or JsonException)
            {
                // Si el archivo está mal, se usa la dirección compilada.
            }
        }

        return new Uri(DefaultApiUrl);
    }
}
