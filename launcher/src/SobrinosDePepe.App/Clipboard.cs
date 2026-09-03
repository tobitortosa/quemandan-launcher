using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Input.Platform;

namespace SobrinosDePepe.App;

/// <summary>Copiar al portapapeles desde un view model, sin arrastrar la ventana.</summary>
public static class Clipboard
{
    public static void Set(string text)
    {
        if (Avalonia.Application.Current?.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
            desktop.MainWindow?.Clipboard?.SetTextAsync(text);
    }
}
