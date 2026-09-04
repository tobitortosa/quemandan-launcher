using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SobrinosDePepe.Core;

namespace SobrinosDePepe.App.ViewModels;

/// <summary>
/// Aparece cuando se publicó una versión nueva del launcher mientras esta estaba
/// abierta. No se puede seguir jugando con una versión vieja: el pack y el launcher
/// tienen que ir juntos, y una versión atrasada instala mal los mods.
///
/// No hay que apretar nada: se avisa, se cierra el juego y se actualiza. Es molesto
/// a propósito, porque es la única forma de que todos estén al día al mismo tiempo.
/// La cuenta regresiva existe para que a nadie se le cierre el juego de golpe.
/// </summary>
public partial class UpdateRequiredViewModel : ObservableObject
{
    /// <summary>Lo que tarda en cerrarse el juego, para poder ponerse a salvo.</summary>
    private const int Segundos = 10;

    private readonly ShellViewModel _shell;

    [ObservableProperty] private string _version;
    [ObservableProperty] private string _message = "";
    [ObservableProperty] private double _percent;
    [ObservableProperty] private bool _hasProgress;
    [ObservableProperty] private bool _isWorking;
    [ObservableProperty] private string? _error;

    public UpdateRequiredViewModel(ShellViewModel shell, string version)
    {
        _shell = shell;
        _version = version;
        _message = "Hay que actualizar para poder jugar.";

        _ = ApplyAsync();
    }

    /// <summary>
    /// El botón queda para reintentar si algo falló. En el camino normal esto ya
    /// corrió solo.
    /// </summary>
    [RelayCommand]
    private Task Update() => ApplyAsync();

    private async Task ApplyAsync()
    {
        if (IsWorking) return;

        IsWorking = true;
        Error = null;

        if (GameProcess.IsRunning())
        {
            for (var quedan = Segundos; quedan > 0; quedan--)
            {
                Message = $"Versión {Version} disponible. El juego se cierra en {quedan}…";

                // Se insiste con la ventana: en pantalla completa el juego se la roba.
                if (quedan % 3 == 0) _shell.ComeToFront();

                await Task.Delay(TimeSpan.FromSeconds(1));
            }

            Message = "Cerrando el juego…";
            await GameProcess.CloseAsync();
        }

        Message = "Bajando la actualización…";

        var progress = new Progress<UpdateProgress>(update =>
        {
            if (update.Stage == UpdateStage.Downloading)
            {
                Percent = update.Percent;
                HasProgress = update.Percent > 0;
                Message = $"Bajando la versión {update.Version}… {update.Percent}%";
            }
            else if (update.Stage == UpdateStage.Applying)
            {
                HasProgress = false;
                Message = "Instalando. El launcher se reinicia solo.";
            }
            else if (update.Stage == UpdateStage.NoConnection)
            {
                Error = "No me pude conectar para bajar la actualización.";
            }
        });

        await Updater.RunAsync(progress);

        // Si llegó hasta acá es que no había nada para aplicar.
        IsWorking = false;
        if (Error is null) _shell.RestartFlow();
    }
}
