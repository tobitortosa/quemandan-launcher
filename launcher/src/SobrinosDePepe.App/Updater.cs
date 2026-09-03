using Velopack;
using Velopack.Sources;

namespace SobrinosDePepe.App;

public enum UpdateStage
{
    Checking,
    Downloading,
    Applying,
    UpToDate,
    NoConnection,
}

public sealed record UpdateProgress(UpdateStage Stage, string? Version = null, int Percent = 0);

/// <summary>
/// El launcher se actualiza solo al abrir, y es obligatorio: todos tienen que estar en
/// la misma versión que el pack publicado. Lo que sí se puede hacer es contarlo mientras
/// pasa, en vez de que la aplicación se cierre y se abra sin explicación.
/// </summary>
public static class Updater
{
    public const string ReleasesUrl = "https://github.com/tobitortosa/sobrinosdepepe-launcher";

    /// <summary>
    /// Busca una versión nueva y, si la hay, la aplica y reinicia la aplicación.
    /// Si no hay ninguna, devuelve el control para seguir con el inicio de sesión.
    /// </summary>
    public static async Task RunAsync(IProgress<UpdateProgress> progress, CancellationToken ct = default)
    {
        progress.Report(new UpdateProgress(UpdateStage.Checking));

        try
        {
            var manager = new UpdateManager(new GithubSource(ReleasesUrl, null, false));

            // Cuando se ejecuta desde la carpeta de compilación no hay nada que actualizar.
            if (!manager.IsInstalled)
            {
                progress.Report(new UpdateProgress(UpdateStage.UpToDate));
                return;
            }

            var update = await manager.CheckForUpdatesAsync().ConfigureAwait(false);
            if (update is null)
            {
                progress.Report(new UpdateProgress(UpdateStage.UpToDate));
                return;
            }

            var version = update.TargetFullRelease.Version.ToString();
            progress.Report(new UpdateProgress(UpdateStage.Downloading, version));

            await manager.DownloadUpdatesAsync(
                update,
                percent => progress.Report(new UpdateProgress(UpdateStage.Downloading, version, percent)),
                ct).ConfigureAwait(false);

            progress.Report(new UpdateProgress(UpdateStage.Applying, version));

            // Da un momento para que se lea el cartel antes de que la ventana desaparezca.
            await Task.Delay(TimeSpan.FromSeconds(1.2), ct).ConfigureAwait(false);
            manager.ApplyUpdatesAndRestart(update);
        }
        catch (Exception)
        {
            // Sin internet no se puede comprobar. Se sigue: el error real va a aparecer
            // al intentar iniciar sesión, que es donde el jugador puede entenderlo.
            progress.Report(new UpdateProgress(UpdateStage.NoConnection));
        }
    }
}
