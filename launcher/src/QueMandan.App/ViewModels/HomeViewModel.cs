using System.Diagnostics;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using QueMandan.Core;

namespace QueMandan.App.ViewModels;

/// <summary>
/// La pantalla con el botón JUGAR. Al apretarlo pide el pack, aplica lo que cambió
/// y abre el juego. Es todo lo que un jugador necesita hacer.
/// </summary>
public partial class HomeViewModel : ObservableObject
{
    private readonly ShellViewModel _shell;
    private readonly string _token;

    [ObservableProperty] private string _username;
    [ObservableProperty] private bool _isAdmin;

    [ObservableProperty] private string _serverLabel = "Consultando el servidor…";
    [ObservableProperty] private bool _serverOnline;
    [ObservableProperty] private bool _serverChecked;

    [ObservableProperty] private bool _isWorking;
    [ObservableProperty] private string _stage = "";
    [ObservableProperty] private string _detail = "";
    [ObservableProperty] private double _percent;
    [ObservableProperty] private bool _hasProgress;

    [ObservableProperty] private string? _error;
    [ObservableProperty] private string? _errorDetail;
    [ObservableProperty] private string? _message;

    public HomeViewModel(ShellViewModel shell, string token, Account account)
    {
        _shell = shell;
        _token = token;
        _username = account.Username;
        _isAdmin = account.IsAdmin;

        var installed = PackInstaller.InstalledVersion();
        Message = installed is null ? "Primera vez: la instalación tarda unos minutos." : $"Pack {installed} instalado.";

        _ = CheckServerAsync();
    }

    private async Task CheckServerAsync()
    {
        var info = await Core.ServerStatus.QueryAsync("quemandan.minehost.pro");
        ServerOnline = info.Online;
        ServerChecked = true;
        ServerLabel = info.Online
            ? $"Servidor online · {info.Players}/{info.MaxPlayers} jugando"
            : "Servidor apagado";
    }

    [RelayCommand]
    private async Task PlayAsync()
    {
        if (IsWorking) return;

        IsWorking = true;
        Error = null;
        ErrorDetail = null;
        Message = null;
        HasProgress = false;
        Stage = "Buscando actualizaciones…";
        Detail = "";

        try
        {
            var pack = await _shell.Api.PackAsync(_token);

            var progress = new Progress<SetupProgress>(p =>
            {
                Stage = p.Stage;
                HasProgress = p.Total > 0;
                Percent = p.Total > 0 ? p.Current * 100.0 / p.Total : 0;
                Detail = p.BytesTotal > 0
                    ? $"{p.Current} de {p.Total} archivos · {p.BytesDone / 1024 / 1024} de {p.BytesTotal / 1024 / 1024} MB"
                    : $"{p.Current} de {p.Total} archivos";
            });

            var detail = new Progress<string>(line => Detail = line);

            var installer = new PackInstaller(
                new GameSetup(LauncherPaths.GameDir, _shell.Http),
                new ModSynchronizer(new HashedDownloader(_shell.Http, backend: (AppConfig.ApiUrl, _token))),
                OverridesDirectory());

            var (version, report) = await installer.ApplyAsync(pack, progress, detail);

            Stage = "Abriendo el juego…";
            Detail = "";
            HasProgress = false;

            var launcher = new GameSetup(LauncherPaths.GameDir, _shell.Http).CreateLauncherWithoutJavaExtractor();
            var runner = new GameRunner(launcher, Path.Combine(LauncherPaths.Root, "game-output.log"));
            var process = runner.BuildProcess(version, Username, pack.Server.Address);

            _ = Task.Run(async () =>
            {
                var run = await runner.RunAsync(process);
                if (run.ExitCode != 0)
                {
                    Error = "El juego se cerró con un error.";
                    ErrorDetail = ReadTail(run.LogPath);
                }
            });

            await Task.Delay(TimeSpan.FromSeconds(6));
            Message = report.WasUpToDate
                ? "Ya estaba todo al día. El juego está abriendo."
                : $"Actualizado: {report.ModsDownloaded} mods nuevos, {report.ModsRemoved} quitados.";
            Stage = "";
        }
        catch (ApiException ex)
        {
            Error = ex.Message;
        }
        catch (Exception ex)
        {
            Error = ex.Message;
            ErrorDetail = ex.ToString();
        }
        finally
        {
            IsWorking = false;
        }
    }

    [RelayCommand]
    private void CopyError()
    {
        var text = $"QUE MANDAN launcher\nUsuario: {Username}\nPack: {PackInstaller.InstalledVersion()}\n\n{Error}\n\n{ErrorDetail}";
        Clipboard.Set(text);
        Message = "Copiado. Pegalo en el chat así lo miramos.";
    }

    [RelayCommand]
    private void OpenFolder() =>
        Process.Start(new ProcessStartInfo("explorer.exe", LauncherPaths.Root) { UseShellExecute = true });

    [RelayCommand]
    private async Task RepairAsync()
    {
        // Reparar es lo mismo que jugar, pero borrando los mods para que se bajen de nuevo.
        try
        {
            if (Directory.Exists(LauncherPaths.ModsDir))
                foreach (var file in Directory.EnumerateFiles(LauncherPaths.ModsDir, "*.jar"))
                    File.Delete(file);
        }
        catch (IOException ex)
        {
            Error = $"No pude limpiar la carpeta de mods: {ex.Message}";
            return;
        }

        await PlayAsync();
    }

    [RelayCommand]
    private void OpenAdmin() => _shell.ShowAdmin(_token, new Account(Username, "active", "admin"));

    [RelayCommand]
    private async Task LogOutAsync()
    {
        try { await _shell.Api.LogoutAsync(_token); } catch (Exception) { /* la sesión local se borra igual */ }
        SessionStore.Clear();
        _shell.ShowLogin("Cerraste sesión.");
    }

    private static string? OverridesDirectory()
    {
        var candidate = Path.Combine(AppContext.BaseDirectory, "overrides");
        return Directory.Exists(candidate) ? candidate : null;
    }

    private static string ReadTail(string path, int lines = 60)
    {
        try
        {
            var all = File.ReadAllLines(path);
            return string.Join('\n', all.Skip(Math.Max(0, all.Length - lines)));
        }
        catch (IOException)
        {
            return "(no pude leer el log)";
        }
    }
}
