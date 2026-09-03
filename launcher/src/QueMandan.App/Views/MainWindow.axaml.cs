using Avalonia.Controls;
using QueMandan.App.ViewModels;

namespace QueMandan.App.Views;

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
