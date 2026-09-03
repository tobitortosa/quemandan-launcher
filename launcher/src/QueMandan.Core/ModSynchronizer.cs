namespace QueMandan.Core;

public sealed record ModSyncResult(int Downloaded, int AlreadyOk, int Removed);

/// <summary>
/// Deja la carpeta mods/ exactamente igual a lo que dice el pack: baja lo que falta
/// y borra lo que no está en la lista. Lo segundo importa: si al quitar un mod del pack
/// el jar sigue en la PC del jugador, el juego crashea al arrancar por incompatibilidad.
/// </summary>
public sealed class ModSynchronizer
{
    private readonly HashedDownloader _downloader;
    public ModSynchronizer(HashedDownloader downloader) => _downloader = downloader;

    public async Task<ModSyncResult> SyncAsync(
        Pack pack,
        string modsDir,
        IProgress<string>? progress = null,
        CancellationToken ct = default)
    {
        Directory.CreateDirectory(modsDir);

        var wanted = pack.ClientMods.ToList();
        var downloaded = 0;
        var alreadyOk = 0;

        foreach (var mod in wanted)
        {
            ct.ThrowIfCancellationRequested();
            var destination = Path.Combine(modsDir, mod.Filename);
            var didDownload = await _downloader.EnsureFileAsync(
                mod.Url, destination, mod.Sha1, mod.Sha512, ct);

            if (didDownload)
            {
                downloaded++;
                progress?.Report($"bajado   {mod.Slug} {mod.VersionNumber}");
            }
            else
            {
                alreadyOk++;
                progress?.Report($"ya está  {mod.Slug} {mod.VersionNumber}");
            }
        }

        var expected = wanted.Select(m => m.Filename).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var removed = 0;
        foreach (var file in Directory.EnumerateFiles(modsDir, "*.jar"))
        {
            if (expected.Contains(Path.GetFileName(file))) continue;
            File.Delete(file);
            removed++;
            progress?.Report($"borrado  {Path.GetFileName(file)} (no está en el pack)");
        }

        return new ModSyncResult(downloaded, alreadyOk, removed);
    }
}
