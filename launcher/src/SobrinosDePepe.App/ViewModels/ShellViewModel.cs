using CommunityToolkit.Mvvm.ComponentModel;
using SobrinosDePepe.Core;

namespace SobrinosDePepe.App.ViewModels;

/// <summary>
/// Decide qué pantalla se ve. Todo el launcher es una ventana que cambia de contenido.
/// </summary>
public partial class ShellViewModel : ObservableObject
{
    private readonly HttpClient _http = HashedDownloader.CreateHttpClient();

    [ObservableProperty]
    private ObservableObject? _current;

    public LauncherApi Api { get; }
    public HttpClient Http => _http;

    public ShellViewModel()
    {
        Api = new LauncherApi(AppConfig.ApiUrl, _http);
        LauncherPaths.EnsureCreated();
        Current = new StartupViewModel();
    }

    /// <summary>
    /// Lo primero que pasa al abrir: se busca una versión nueva del launcher y, si la
    /// hay, se instala y la aplicación se reinicia. Después se entra con la sesión
    /// guardada, o se pide iniciar sesión.
    /// </summary>
    public async Task StartAsync()
    {
        var startup = Current as StartupViewModel ?? new StartupViewModel();
        Current = startup;

        await Updater.RunAsync(new Progress<UpdateProgress>(startup.Report));

        startup.EnteringSession();
        await ResumeSessionAsync();

        // Si no había sesión guardada, se pide iniciar sesión.
        if (Current == startup) ShowLogin();
    }

    public void ShowLogin(string? message = null) =>
        Current = new LoginViewModel(this) { Notice = message };

    public void ShowPending(string token, Account account) =>
        Current = new PendingViewModel(this, token, account);

    public void ShowHome(string token, Account account) =>
        Current = new HomeViewModel(this, token, account);

    public void ShowAdmin(string token, Account account) =>
        Current = new AdminViewModel(this, token, account);

    /// <summary>Al arrancar, si hay una sesión guardada se entra sin preguntar nada.</summary>
    public async Task ResumeSessionAsync()
    {
        var token = SessionStore.Load();
        if (token is null) return;

        try
        {
            var account = await Api.AccountAsync(token);
            Route(token, account);
        }
        catch (ApiException)
        {
            // La sesión venció o la cuenta cambió: se pide login de nuevo.
            SessionStore.Clear();
        }
        catch (HttpRequestException)
        {
            // Sin conexión no se puede validar la sesión: se muestra el login.
            SessionStore.Clear();
        }
    }

    public void Route(string token, Account account)
    {
        // Elegir la contraseña propia va antes que todo lo demás.
        if (account.MustChangePassword) Current = new ChangePasswordViewModel(this, token, account);
        else if (account.IsPending) ShowPending(token, account);
        else ShowHome(token, account);
    }
}
