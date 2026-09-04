using Avalonia.Media;
using SobrinosDePepe.Core;

namespace SobrinosDePepe.App.ViewModels;

/// <summary>
/// Una fila de la lista de cuentas. Sabe quién sos vos y quién está jugando en este
/// momento, y con eso decide qué mostrar: a un administrador no se lo banea, y sobre
/// tu propia cuenta no se genera una contraseña nueva, que te dejaría afuera.
/// </summary>
public sealed class UserRow(AdminUser user, string currentUsername, bool isOnline)
{
    public AdminUser User { get; } = user;

    public int Id => User.Id;
    public string Username => User.Username;
    public string Status => User.Status;
    public DateTimeOffset CreatedAt => User.CreatedAt;
    public bool IsAdmin => User.IsAdmin;

    public bool IsMe { get; } = string.Equals(user.Username, currentUsername, StringComparison.Ordinal);

    /// <summary>Está conectado al servidor ahora mismo.</summary>
    public bool IsOnline { get; } = isOnline;

    public bool CanApprove => User.IsPending;
    public bool CanBan => User.IsActive && !User.IsAdmin;
    public bool CanUnban => User.IsBanned;
    public bool CanResetPassword => !IsMe;

    /// <summary>
    /// El verde queda para quien está jugando. Una cuenta habilitada pero desconectada
    /// se ve apagada: así se distingue de un vistazo quién está adentro.
    /// </summary>
    public IBrush Dot => new SolidColorBrush(Color.Parse(Status switch
    {
        "pending" => "#F5A524",
        "banned" => "#F87171",
        "active" when IsOnline => "#4ADE80",
        "active" => "#3F4652",
        _ => "#9AA0AA",
    }));

    public string StatusLabel => Status switch
    {
        "pending" => "pendiente",
        "banned" => "baneado",
        "active" when IsOnline => "jugando ahora",
        "active" => "habilitado",
        _ => Status,
    };
}
