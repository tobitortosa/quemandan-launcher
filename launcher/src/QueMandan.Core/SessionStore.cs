using System.Security.Cryptography;
using System.Text;

namespace QueMandan.Core;

/// <summary>
/// Guarda el token de la sesión en el disco, cifrado con la cuenta de Windows del
/// jugador. No se guarda la contraseña en ningún momento.
/// </summary>
public static class SessionStore
{
    private static readonly byte[] Salt = Encoding.UTF8.GetBytes("QueMandanLauncher");

    public static void Save(string token)
    {
        Directory.CreateDirectory(LauncherPaths.Root);
        var encrypted = ProtectedData.Protect(
            Encoding.UTF8.GetBytes(token), Salt, DataProtectionScope.CurrentUser);
        File.WriteAllBytes(LauncherPaths.SessionFile, encrypted);
    }

    public static string? Load()
    {
        if (!File.Exists(LauncherPaths.SessionFile)) return null;

        try
        {
            var decrypted = ProtectedData.Unprotect(
                File.ReadAllBytes(LauncherPaths.SessionFile), Salt, DataProtectionScope.CurrentUser);
            var token = Encoding.UTF8.GetString(decrypted);
            return string.IsNullOrWhiteSpace(token) ? null : token;
        }
        catch (Exception ex) when (ex is CryptographicException or IOException)
        {
            // El archivo no se puede descifrar (otro usuario de Windows, u otra PC).
            Clear();
            return null;
        }
    }

    public static void Clear()
    {
        try
        {
            if (File.Exists(LauncherPaths.SessionFile)) File.Delete(LauncherPaths.SessionFile);
        }
        catch (IOException)
        {
        }
    }
}
