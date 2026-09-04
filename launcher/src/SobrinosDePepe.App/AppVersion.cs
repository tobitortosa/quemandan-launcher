namespace SobrinosDePepe.App;

/// <summary>
/// La versión del launcher: la misma que dice el release. Se ve abajo de todo en
/// cada pantalla, así una captura de pantalla ya cuenta qué versión tiene puesta
/// quien la mandó. No es la del pack de mods, que cambia por su cuenta.
/// </summary>
public static class AppVersion
{
    /// <summary>La pone pack-release.ps1 al compilar, con el mismo número que publica.</summary>
    public static Version Current { get; } =
        typeof(AppVersion).Assembly.GetName().Version ?? new Version(0, 0, 0);

    /// <summary>Queda como "v1.9.1".</summary>
    public static string Label { get; } = $"v{Current.Major}.{Current.Minor}.{Current.Build}";

    /// <summary>
    /// En una compilación de desarrollo la versión queda en cero. Ahí no se vigila:
    /// cualquier release publicada parecería más nueva y la pantalla de actualización
    /// obligatoria no se iría nunca.
    /// </summary>
    public static bool IsPublished => Current.Major > 0;
}
