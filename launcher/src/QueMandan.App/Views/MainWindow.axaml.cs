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
        Opened += async (_, _) => await _shell.ResumeSessionAsync();
    }
}
