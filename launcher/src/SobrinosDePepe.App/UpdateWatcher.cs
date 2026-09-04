using Velopack;
using Velopack.Sources;

namespace SobrinosDePepe.App;

/// <summary>
/// Mira cada tanto si se publicó una versión nueva del launcher. Alcanza con preguntar
/// cada pocos minutos: no hace falta mantener una conexión abierta para algo que pasa
/// una vez por semana, y una consulta simple no se corta ni hay que reconectarla.
/// </summary>
public static class UpdateWatcher
{
    private static readonly TimeSpan Interval = TimeSpan.FromMinutes(5);

    /// <summary>
    /// Avisa una sola vez, con la versión encontrada, cuando aparece una nueva.
    /// </summary>
    public static void Start(Action<string> onFound, CancellationToken ct = default)
    {
        _ = Task.Run(async () =>
        {
            while (!ct.IsCancellationRequested)
            {
                await Task.Delay(Interval, ct);

                try
                {
                    var manager = new UpdateManager(new GithubSource(Updater.ReleasesUrl, null, false));
                    if (!manager.IsInstalled) continue;

                    var update = await manager.CheckForUpdatesAsync();
                    if (update is null) continue;

                    onFound(update.TargetFullRelease.Version.ToString());
                    return;
                }
                catch (Exception)
                {
                    // Sin internet se vuelve a intentar en el próximo turno.
                }
            }
        }, ct);
    }
}
