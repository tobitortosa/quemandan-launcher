using Velopack;
using Velopack.Sources;

namespace QueMandan.App;

/// <summary>
/// El launcher se actualiza solo al abrir. Sin esto, cada arreglo obligaría a que
/// cada jugador vuelva a bajar el instalador a mano, y los que no lo hagan van a
/// fallar de formas raras.
/// </summary>
public static class Updater
{
    /// <summary>El repositorio desde donde salen las versiones nuevas.</summary>
    public const string ReleasesUrl = "https://github.com/tobitortosa/quemandan-launcher";

    /// <summary>
    /// Busca una versión nueva y la deja lista. Devuelve la versión encontrada, o null
    /// si ya estaba al día. Si algo falla, no interrumpe: el jugador puede jugar igual.
    /// </summary>
    public static async Task<string?> CheckAsync()
    {
        try
        {
            var manager = new UpdateManager(new GithubSource(ReleasesUrl, null, false));
            if (!manager.IsInstalled) return null;

            var update = await manager.CheckForUpdatesAsync();
            if (update is null) return null;

            await manager.DownloadUpdatesAsync(update);
            manager.ApplyUpdatesAndRestart(update);
            return update.TargetFullRelease.Version.ToString();
        }
        catch (Exception)
        {
            return null;
        }
    }
}
