using SobrinosDePepe.Core;

namespace SobrinosDePepe.App;

/// <summary>
/// Vigila que la máquina del jugador esté al día, tanto el launcher como el pack de
/// mods. Pregunta cada diez segundos, y le pregunta al backend en vez de a GitHub:
/// la API de GitHub corta a las sesenta consultas por hora y cada diez segundos son
/// trescientas sesenta.
///
/// Las dos cosas son obligatorias. Un launcher viejo instala mal el pack, y un pack
/// que no coincide con el del servidor no deja entrar: por eso, cuando aparece algo
/// nuevo, al jugador se lo saca del juego en vez de dejarlo seguir.
/// </summary>
public static class UpdateWatcher
{
    private static readonly TimeSpan Interval = TimeSpan.FromSeconds(10);

    /// <summary>
    /// <paramref name="onLauncher"/> avisa una sola vez, porque después de actualizar
    /// el launcher se reinicia. <paramref name="onPack"/> avisa una vez por versión y
    /// sigue vigilando, porque el pack se sincroniza sin cerrar el launcher.
    /// </summary>
    public static void Start(
        LauncherApi api, Action<string> onLauncher, Action<string> onPack, CancellationToken ct = default)
    {
        _ = Task.Run(async () =>
        {
            string? packAvisado = null;

            while (!ct.IsCancellationRequested)
            {
                await Task.Delay(Interval, ct);

                try
                {
                    var versions = await api.VersionsAsync(ct);

                    if (AppVersion.IsPublished && EsMasNueva(versions.Launcher))
                    {
                        onLauncher(versions.Launcher!);
                        return;
                    }

                    var instalado = PackInstaller.InstalledVersion();
                    if (versions.Pack is not null && instalado is not null &&
                        versions.Pack != instalado && versions.Pack != packAvisado)
                    {
                        packAvisado = versions.Pack;
                        onPack(versions.Pack);
                    }
                }
                catch (Exception)
                {
                    // Sin internet se vuelve a intentar en el próximo turno.
                }
            }
        }, ct);
    }

    private static bool EsMasNueva(string? publicada) =>
        Version.TryParse(publicada, out var version) && version > AppVersion.Current;
}
