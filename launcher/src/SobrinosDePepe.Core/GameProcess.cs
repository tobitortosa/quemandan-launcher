using System.Diagnostics;
using System.Runtime.InteropServices;

namespace SobrinosDePepe.Core;

/// <summary>
/// Encuentra el Minecraft que este launcher abrió y lo trae al frente.
///
/// Importa que no haya dos abiertos a la vez: los dos escribirían en la misma carpeta,
/// y eso corrompe los mundos y las configuraciones. Además, si alguien sale del servidor
/// pero deja el juego abierto, lo que quiere al apretar JUGAR es volver a la ventana que
/// ya tiene, no esperar otros veinte segundos de carga.
/// </summary>
public static class GameProcess
{
    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr handle);

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr handle, int command);

    [DllImport("user32.dll")]
    private static extern bool IsIconic(IntPtr handle);

    private const int Restore = 9;

    /// <summary>
    /// El proceso del juego, si hay uno corriendo desde nuestra carpeta. Busca por la
    /// ruta del ejecutable y no por el nombre, así no se confunde con otro Minecraft
    /// que la persona tenga abierto por su cuenta.
    /// </summary>
    public static Process? Find()
    {
        var ours = Path.GetFullPath(LauncherPaths.GameDir);

        // Se buscan solo los procesos de Java, no todos los del sistema.
        foreach (var name in new[] { "javaw", "java" })
        {
            foreach (var process in Process.GetProcessesByName(name))
            {
                try
                {
                    var path = process.MainModule?.FileName;
                    if (path is not null && Path.GetFullPath(path).StartsWith(ours, StringComparison.OrdinalIgnoreCase))
                        return process;
                }
                catch (Exception)
                {
                    // Un proceso de otro usuario o que acaba de terminar: no es el nuestro.
                }

                process.Dispose();
            }
        }

        return null;
    }

    public static bool IsRunning()
    {
        using var process = Find();
        return process is not null;
    }

    /// <summary>
    /// Espera hasta que el juego abra su ventana. Java tarda: en una máquina lenta
    /// pasan treinta o cuarenta segundos entre arrancar el proceso y ver algo en
    /// pantalla, y durante ese rato el jugador no sabe si algo está pasando.
    /// </summary>
    /// <returns>
    /// true cuando el juego está andando, ya sea porque apareció la ventana o porque
    /// se agotó la espera y el proceso sigue vivo. false solo si el proceso terminó,
    /// que es lo que ocurre cuando el juego falla al arrancar.
    /// </returns>
    public static async Task<bool> WaitForWindowAsync(Process process, TimeSpan? limit = null)
    {
        var deadline = DateTime.UtcNow + (limit ?? TimeSpan.FromMinutes(3));

        while (true)
        {
            try
            {
                process.Refresh();

                if (process.HasExited) return false;
                if (process.MainWindowHandle != IntPtr.Zero) return true;
                if (DateTime.UtcNow >= deadline) return true;
            }
            catch (InvalidOperationException)
            {
                return false;
            }

            await Task.Delay(TimeSpan.FromMilliseconds(400));
        }
    }

    /// <summary>Trae la ventana del juego al frente, y la restaura si estaba minimizada.</summary>
    public static bool BringToFront()
    {
        using var process = Find();
        var handle = process?.MainWindowHandle ?? IntPtr.Zero;
        if (handle == IntPtr.Zero) return false;

        if (IsIconic(handle)) ShowWindow(handle, Restore);
        return SetForegroundWindow(handle);
    }

    /// <summary>Cierra el juego. Primero pide cerrar bien; si no responde, lo termina.</summary>
    public static async Task<bool> CloseAsync(CancellationToken ct = default)
    {
        using var process = Find();
        if (process is null) return false;

        try
        {
            process.CloseMainWindow();
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(ct);
            timeout.CancelAfter(TimeSpan.FromSeconds(8));
            await process.WaitForExitAsync(timeout.Token);
        }
        catch (OperationCanceledException)
        {
            try { process.Kill(entireProcessTree: true); } catch (Exception) { }
        }
        catch (Exception)
        {
        }

        return true;
    }
}
