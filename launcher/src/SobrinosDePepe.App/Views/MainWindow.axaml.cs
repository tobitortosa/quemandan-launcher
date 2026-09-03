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
        Opened += async (_, _) => await _shell.StartAsync();
    }
}
