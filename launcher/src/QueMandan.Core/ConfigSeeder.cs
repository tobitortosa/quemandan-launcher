namespace QueMandan.Core;

public sealed record ConfigSeedResult(int Written, int Kept);

/// <summary>
/// Copia las configuraciones del pack, pero solo las que no existen todavía.
/// La regla es a propósito: ahí viven los controles, la sensibilidad del mouse, los
/// waypoints y el volumen de cada jugador. Si se pisaran en cada actualización del pack,
/// cada publicación les borraría sus ajustes.
/// A diferencia de esto, la carpeta mods/ sí se sincroniza siempre.
/// </summary>
public static class ConfigSeeder
{
    /// <summary>Archivos que son de la máquina o de la cuenta y nunca se distribuyen.</summary>
    private static readonly string[] NeverCopy =
    [
        "sodium-fingerprint.json",
        "username-cache.json",
        "usercache.json"
    ];

    public static ConfigSeedResult Seed(string overridesDir, string gameDir, IProgress<string>? progress = null)
    {
        if (!Directory.Exists(overridesDir))
            return new ConfigSeedResult(0, 0);

        var written = 0;
        var kept = 0;

        foreach (var source in Directory.EnumerateFiles(overridesDir, "*", SearchOption.AllDirectories))
        {
            var name = Path.GetFileName(source);
            if (NeverCopy.Contains(name, StringComparer.OrdinalIgnoreCase))
                continue;

            var relative = Path.GetRelativePath(overridesDir, source);
            var destination = Path.Combine(gameDir, relative);

            if (File.Exists(destination))
            {
                kept++;
                continue;
            }

            Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
            File.Copy(source, destination);
            written++;
            progress?.Report($"config   {relative}");
        }

        return new ConfigSeedResult(written, kept);
    }
}
