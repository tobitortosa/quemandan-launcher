using CmlLib.Core;
using CmlLib.Core.FileExtractors;
using CmlLib.Core.Installers;
using CmlLib.Core.Java;
using CmlLib.Core.ModLoaders.FabricMC;
using CmlLib.Core.Rules;
using CmlLib.Core.Version;
using CmlLib.Core.VersionLoader;

namespace QueMandan.Core;

public sealed record SetupProgress(string Stage, string Detail, int Current, int Total, long BytesDone, long BytesTotal);

/// <summary>
/// Instala Minecraft, el Java que corresponde y el perfil de Fabric en la carpeta propia.
/// Todo se descarga de los servidores oficiales de Mojang y de Fabric a la PC del jugador.
/// </summary>
public sealed class GameSetup
{
    private readonly MinecraftPath _path;
    private readonly HttpClient _http;

    public GameSetup(string gameDir, HttpClient http)
    {
        _path = new MinecraftPath(gameDir);
        _http = http;
    }

    public MinecraftPath Path => _path;

    /// <summary>
    /// Instala la versión vanilla (cliente, librerías, assets) y el runtime de Java que
    /// declara esa versión. Para 26.1 eso es Java 25, así que no importa qué Java tenga
    /// instalado el jugador ni si no tiene ninguno.
    /// </summary>
    public async Task<IVersion> InstallVanillaAsync(
        string minecraftVersion,
        IProgress<SetupProgress>? progress,
        CancellationToken ct = default)
    {
        var launcher = new MinecraftLauncher(MinecraftLauncherParameters.CreateDefault(_path, _http));

        var files = 0;
        var filesTotal = 0;
        var bytes = 0L;
        var bytesTotal = 0L;
        var stage = "Minecraft " + minecraftVersion;

        var fileProgress = new Progress<InstallerProgressChangedEventArgs>(e =>
        {
            files = e.ProgressedTasks;
            filesTotal = e.TotalTasks;
            progress?.Report(new SetupProgress(stage, e.Name ?? "", files, filesTotal, bytes, bytesTotal));
        });
        var byteProgress = new Progress<ByteProgress>(e =>
        {
            bytes = e.ProgressedBytes;
            bytesTotal = e.TotalBytes;
            progress?.Report(new SetupProgress(stage, "", files, filesTotal, bytes, bytesTotal));
        });

        await launcher.InstallAsync(minecraftVersion, fileProgress, byteProgress, ct);
        return await launcher.GetVersionAsync(minecraftVersion, ct);
    }

    /// <summary>
    /// Escribe el perfil de Fabric y descarga solo sus librerías.
    /// </summary>
    /// <remarks>
    /// El perfil de Fabric no declara qué Java necesita, lo hereda de la versión vanilla.
    /// La librería, si le pedimos instalar el perfil completo, interpreta esa ausencia como
    /// "Java 8" y se baja 150 MB de un runtime viejo que no se usa nunca. Por eso acá se
    /// arma un instalador sin el extractor de Java y se instalan únicamente los archivos
    /// propios del perfil.
    /// </remarks>
    public async Task<IVersion> InstallFabricAsync(
        string minecraftVersion,
        string loaderVersion,
        IProgress<SetupProgress>? progress,
        CancellationToken ct = default)
    {
        var installer = new FabricInstaller(_http);
        var versionName = await installer.Install(minecraftVersion, loaderVersion, _path);

        var launcher = CreateLauncherWithoutJavaExtractor();
        var version = await launcher.GetVersionAsync(versionName, ct);

        // ExtractFiles sobre esta única versión: no vuelve a recorrer la versión vanilla,
        // que ya quedó instalada y verificada en el paso anterior.
        var files = await launcher.ExtractFiles(version, ct);

        var count = 0;
        var list = files.ToList();
        var fileProgress = new Progress<InstallerProgressChangedEventArgs>(e =>
        {
            count = e.ProgressedTasks;
            progress?.Report(new SetupProgress("Fabric " + loaderVersion, e.Name ?? "", count, e.TotalTasks, 0, 0));
        });

        await launcher.GameInstaller.Install(list, fileProgress, null, ct);
        return version;
    }

    public MinecraftLauncher CreateLauncherWithoutJavaExtractor()
    {
        var parameters = MinecraftLauncherParameters.CreateDefault(_path, _http);
        var rules = new RulesEvaluator();
        var javaResolver = new MinecraftJavaPathResolver(_path);
        var extractors = DefaultFileExtractors.CreateDefault(_http, rules, javaResolver);
        extractors.Java = null;
        parameters.RulesEvaluator = rules;
        parameters.JavaPathResolver = javaResolver;
        parameters.FileExtractors = extractors.ToExtractorCollection();
        parameters.VersionLoader = new MojangJsonVersionLoaderV2(_path, _http);
        parameters.GameInstaller = ParallelGameInstaller.CreateAsCoreCount(_http);
        return new MinecraftLauncher(parameters);
    }

    public static string FabricVersionName(string minecraftVersion, string loaderVersion) =>
        FabricInstaller.GetVersionName(minecraftVersion, loaderVersion);
}
