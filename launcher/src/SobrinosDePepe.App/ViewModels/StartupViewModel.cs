using CommunityToolkit.Mvvm.ComponentModel;

namespace SobrinosDePepe.App.ViewModels;

/// <summary>
/// La primera pantalla. Cuenta qué está haciendo el launcher antes de pedir la
/// contraseña: buscar una versión nueva, bajarla, o entrar directo si ya está al día.
/// </summary>
public partial class StartupViewModel : ObservableObject
{
    [ObservableProperty] private string _message = "Buscando actualizaciones…";
    [ObservableProperty] private string? _detail;
    [ObservableProperty] private double _percent;
    [ObservableProperty] private bool _hasProgress;

    public void Report(UpdateProgress update)
    {
        switch (update.Stage)
        {
            case UpdateStage.Checking:
                Message = "Buscando actualizaciones…";
                Detail = null;
                HasProgress = false;
                break;

            case UpdateStage.Downloading:
                Message = $"Bajando la versión {update.Version}";
                Detail = update.Percent > 0 ? $"{update.Percent}%" : "empezando…";
                Percent = update.Percent;
                HasProgress = update.Percent > 0;
                break;

            case UpdateStage.Applying:
                Message = "Instalando la actualización";
                Detail = "El launcher se va a reiniciar solo.";
                HasProgress = false;
                break;

            case UpdateStage.UpToDate:
                Message = "Todo al día";
                Detail = null;
                HasProgress = false;
                break;

            case UpdateStage.NoConnection:
                Message = "Sin conexión";
                Detail = "No pude comprobar si hay una versión nueva.";
                HasProgress = false;
                break;
        }
    }

    public void EnteringSession()
    {
        Message = "Entrando…";
        Detail = null;
        HasProgress = false;
    }
}
