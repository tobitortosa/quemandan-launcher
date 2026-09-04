using Avalonia.Controls;
using SobrinosDePepe.App.ViewModels;
using SobrinosDePepe.Core;

namespace SobrinosDePepe.App.Views;

public partial class MainWindow : Window
{
    private readonly ShellViewModel _shell = new();

    public MainWindow()
    {
        InitializeComponent();
        DataContext = _shell;

        Opened += async (_, _) => await _shell.StartAsync();

        // Cuando aparece una versión nueva, la ventana se pone adelante: si no, alguien
        // jugando en pantalla completa no se enteraría nunca. Puede estar minimizada,
        // así que primero hay que restaurarla.
        _shell.BringToFront += () =>
        {
            if (WindowState == WindowState.Minimized) WindowState = WindowState.Normal;
            Show();
            Activate();
        };

        // La pantalla de actualización obligatoria se queda encima del juego. Sin esto
        // el juego recupera el foco enseguida y el aviso no se ve nunca.
        _shell.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(ShellViewModel.Current))
                Topmost = _shell.Current is UpdateRequiredViewModel;
        };

        // No se cierra el launcher con el juego abierto. Al cerrarse dejaría de avisar
        // de las actualizaciones, y son obligatorias.
        Closing += (_, e) =>
        {
            if (!GameProcess.IsRunning()) return;

            e.Cancel = true;
            Activate();
            _shell.NotifyCannotClose();
        };
    }
}
