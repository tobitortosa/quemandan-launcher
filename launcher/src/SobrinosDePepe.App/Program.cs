using Avalonia;
using Velopack;

namespace SobrinosDePepe.App;

internal static class Program
{
    [STAThread]
    public static void Main(string[] args)
    {
        // Velopack maneja la instalación y las actualizaciones. Tiene que ser lo primero
        // que corra: en el arranque posterior a una actualización, esta llamada termina
        // el trabajo y reinicia la aplicación.
        VelopackApp.Build().Run();

        BuildAvaloniaApp().StartWithClassicDesktopLifetime(args);
    }

    public static AppBuilder BuildAvaloniaApp() =>
        AppBuilder.Configure<Application>()
            .UsePlatformDetect()
            .WithInterFont()
            .LogToTrace();
}
