using Avalonia.Controls;
using SobrinosDePepe.App.ViewModels;

namespace SobrinosDePepe.App.Views;

public partial class MainWindow : Window
{
    private readonly ShellViewModel _shell = new();

    public MainWindow()
    {
        InitializeComponent();
        DataContext = _shell;
        Opened += async (_, _) =>
        {
            // Si hay una versión nueva del launcher, se aplica y la app se reinicia sola.
            await Updater.CheckAsync();
            await _shell.ResumeSessionAsync();
        };
    }
}
