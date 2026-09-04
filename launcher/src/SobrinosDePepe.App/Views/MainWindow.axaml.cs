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
        // jugando en pantalla completa no se enteraría nunca.
        _shell.BringToFront += () =>
        {
            Topmost = true;
            Activate();
            Topmost = false;
        };

        // No se cierra el launcher con el juego abierto. Al cerrarse dejaría de avisar
        // de las actualizaciones, y son obligatorias.
        Closing += (_, e) =>
        {
            if (!GameProcess.IsRunning()) return;

            e.Cancel = true;
            Topmost = true;
            Activate();
            Topmost = false;
            _shell.NotifyCannotClose();
        };
    }
}
