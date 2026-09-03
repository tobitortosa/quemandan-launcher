using System.Collections.ObjectModel;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Platform.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SobrinosDePepe.Core;

namespace SobrinosDePepe.App.ViewModels;

/// <summary>
/// El panel de administración, dentro del mismo launcher. Dos cosas: las cuentas y
/// los mods. Ninguna acción se hace acá: todas se le piden al backend, que verifica
/// el rol y es el único que puede hablarle al servidor de Minecraft.
/// </summary>
public partial class AdminViewModel : ObservableObject
{
    private readonly ShellViewModel _shell;
    private readonly string _token;

    [ObservableProperty] private string _username;
    [ObservableProperty] private int _tab;          // 0 = usuarios, 1 = mods
    [ObservableProperty] private bool _isBusy;
    [ObservableProperty] private string? _error;
    [ObservableProperty] private string? _notice;

    // Confirmación de las acciones que no se pueden deshacer.
    [ObservableProperty] private string? _confirmText;
    private Func<Task>? _pendingAction;

    // Usuarios
    public ObservableCollection<UserRow> Users { get; } = [];
    [ObservableProperty] private string _search = "";
    [ObservableProperty] private int _pendingCount;

    // Mods
    public ObservableCollection<AdminMod> Mods { get; } = [];
    [ObservableProperty] private string _packVersion = "—";
    [ObservableProperty] private string _packInfo = "";
    [ObservableProperty] private bool _hasUnpublishedChanges;
    [ObservableProperty] private string? _serverSideNote;

    public AdminViewModel(ShellViewModel shell, string token, Account account)
    {
        _shell = shell;
        _token = token;
        _username = account.Username;
        _ = LoadUsersAsync();
        _ = LoadModsAsync();
    }

    public bool ShowingUsers => Tab == 0;
    public bool ShowingMods => Tab == 1;

    partial void OnTabChanged(int value)
    {
        OnPropertyChanged(nameof(ShowingUsers));
        OnPropertyChanged(nameof(ShowingMods));
    }

    [RelayCommand]
    private void ShowUsers() => Tab = 0;

    [RelayCommand]
    private void ShowMods() => Tab = 1;

    [RelayCommand]
    private void Back() => _shell.ShowHome(_token, new Account(Username, "active", "admin"));

    // ----------------------------------------------------------------- Usuarios

    [RelayCommand]
    private async Task LoadUsersAsync()
    {
        await RunAsync(async () =>
        {
            var users = await _shell.Api.UsersAsync(_token, Search);
            Users.Clear();
            foreach (var user in users) Users.Add(new UserRow(user, Username));
            PendingCount = users.Count(u => u.IsPending);
        });
    }

    [RelayCommand]
    private async Task ApproveAsync(UserRow user)
    {
        await RunAsync(async () =>
        {
            await _shell.Api.ApproveAsync(_token, user.Id);
            Notice = $"{user.Username} aprobado y agregado a la whitelist.";
            await LoadUsersAsync();
        });
    }

    [RelayCommand]
    private void Ban(UserRow user) =>
        Ask($"¿Banear a {user.Username}? Lo sacamos de la whitelist y lo echamos del servidor.",
            async () =>
            {
                await _shell.Api.BanAsync(_token, user.Id, "Baneado");
                Notice = $"{user.Username} baneado, sacado de la whitelist y echado del servidor.";
                await LoadUsersAsync();
            });

    [RelayCommand]
    private async Task UnbanAsync(UserRow user)
    {
        await RunAsync(async () =>
        {
            await _shell.Api.UnbanAsync(_token, user.Id);
            Notice = $"{user.Username} vuelve a estar habilitado.";
            await LoadUsersAsync();
        });
    }

    [RelayCommand]
    private void ResetPassword(UserRow user) =>
        Ask($"¿Generar una contraseña nueva para {user.Username}? La actual deja de funcionar y se cierran sus sesiones.",
            async () =>
            {
                var result = await _shell.Api.ResetPasswordAsync(_token, user.Id);
                Clipboard.Set(result.Password);
                Notice = $"Contraseña nueva de {result.Username}: {result.Password} (copiada, pasásela)";
            });

    // --------------------------------------------------------------------- Mods

    [RelayCommand]
    private async Task LoadModsAsync()
    {
        await RunAsync(async () =>
        {
            var draft = await _shell.Api.PackDraftAsync(_token);
            Mods.Clear();
            foreach (var mod in draft.Mods) Mods.Add(mod);

            PackVersion = draft.PublishedVersion ?? "sin publicar";
            PackInfo = $"Minecraft {draft.Minecraft} · Fabric {draft.FabricLoader} · {draft.Mods.Count} mods";
            HasUnpublishedChanges = draft.HasUnpublishedChanges;
            ServerSideNote = draft.ServerSide.Count > 0
                ? $"{draft.ServerSide.Count} de estos van también en el servidor"
                : null;
        });
    }

    [RelayCommand]
    private async Task AddModsAsync()
    {
        var window = (Avalonia.Application.Current?.ApplicationLifetime as IClassicDesktopStyleApplicationLifetime)?.MainWindow;
        if (window is null) return;

        var files = await window.StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
        {
            Title = "Elegí los mods (.jar)",
            AllowMultiple = true,
            FileTypeFilter = [new FilePickerFileType("Mods de Minecraft") { Patterns = ["*.jar"] }],
        });

        var paths = files
            .Select(f => f.TryGetLocalPath())
            .Where(p => !string.IsNullOrEmpty(p))
            .Select(p => p!)
            .ToList();

        if (paths.Count == 0) return;

        await RunAsync(async () =>
        {
            var result = await _shell.Api.UploadModsAsync(_token, paths);

            var lines = new List<string>();
            if (result.Added.Count > 0)
                lines.Add($"{result.Added.Count} agregados: " +
                          string.Join(", ", result.Added.Select(a => $"{a.Title} {a.Version}")));
            foreach (var bad in result.Rejected)
                lines.Add($"{bad.Filename}: {bad.Reason}");
            foreach (var note in result.Added.Where(a => a.Note is not null))
                lines.Add(note.Note!);

            Notice = string.Join("\n", lines);
            await LoadModsAsync();
        });
    }

    [RelayCommand]
    private void RemoveMod(AdminMod mod) =>
        Ask($"¿Quitar {mod.Title} del pack? Se les borra a todos cuando publiques.",
            async () =>
            {
                await _shell.Api.RemoveModAsync(_token, mod.ProjectId);
                Notice = $"{mod.Title} quitado del pack. Publicá para que les llegue a todos.";
                await LoadModsAsync();
            });

    /// <summary>Deja una acción esperando el sí. Un clic de más no rompe nada.</summary>
    private void Ask(string question, Func<Task> action)
    {
        ConfirmText = question;
        _pendingAction = action;
    }

    [RelayCommand]
    private async Task ConfirmAsync()
    {
        var action = _pendingAction;
        ConfirmText = null;
        _pendingAction = null;
        if (action is not null) await RunAsync(action);
    }

    [RelayCommand]
    private void CancelConfirm()
    {
        ConfirmText = null;
        _pendingAction = null;
    }

    [RelayCommand]
    private async Task PublishAsync()
    {
        await RunAsync(async () =>
        {
            var result = await _shell.Api.PublishAsync(_token);
            Notice = $"Pack {result.Version} publicado con {result.Mods} mods. " +
                     "Cada jugador lo recibe al apretar JUGAR.";
            if (result.ServerSide.Count > 0)
                Notice += "\n\nEstos van también en el servidor, por SFTP a /mods:\n" +
                          string.Join("\n", result.ServerSide);
            await LoadModsAsync();
        });
    }

    // ------------------------------------------------------------------ Común

    private async Task RunAsync(Func<Task> action)
    {
        if (IsBusy) return;
        IsBusy = true;
        Error = null;

        try
        {
            await action();
        }
        catch (ApiException ex)
        {
            Error = ex.Message;
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
        {
            Error = "No me pude conectar con el backend.";
        }
        catch (Exception ex)
        {
            Error = ex.Message;
        }
        finally
        {
            IsBusy = false;
        }
    }
}
