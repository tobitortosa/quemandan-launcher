using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SobrinosDePepe.Core;

namespace SobrinosDePepe.App.ViewModels;

/// <summary>
/// Aparece cuando se publicó una versión nueva del launcher mientras esta estaba
/// abierta. No se puede seguir jugando con una versión vieja: el pack y el launcher
/// tienen que ir juntos, y una versión atrasada instala mal los mods.
///
/// Si el juego está abierto, esta pantalla se trae al frente. Es molesto a propósito:
/// es la única forma de que alguien que está jugando se entere.
/// </summary>
public partial class UpdateRequiredViewModel : ObservableObject
{
    private readonly ShellViewModel _shell;

    [ObservableProperty] private string _version;
    [ObservableProperty] private string _message = "";
    [ObservableProperty] private double _percent;
    [ObservableProperty] private bool _hasProgress;
    [ObservableProperty] private bool _isWorking;
    [ObservableProperty] private bool _gameIsOpen;
    [ObservableProperty] private string? _error;

    public UpdateRequiredViewModel(ShellViewModel shell, string version)
    {
        _shell = shell;
        _version = version;
        _gameIsOpen = GameProcess.IsRunning();
        _message = GameIsOpen
            ? "Podés seguir jugando esta partida, pero para volver a entrar hay que actualizar."
            : "Hay que actualizar para poder jugar.";
    }

    [RelayCommand]
    private async Task UpdateAsync()
    {
        IsWorking = true;
        Error = null;
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
