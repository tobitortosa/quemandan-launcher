using QueMandan.Core;

namespace QueMandan.App.ViewModels;

/// <summary>
/// Una fila de la lista de cuentas. Sabe quién sos vos, y con eso decide qué botones
/// tiene sentido mostrar: a un administrador no se lo banea, y sobre tu propia cuenta
/// no se genera una contraseña nueva (te dejaría afuera en el momento).
/// </summary>
public sealed class UserRow(AdminUser user, string currentUsername)
{
    public AdminUser User { get; } = user;

    public int Id => User.Id;
    public string Username => User.Username;
    public string StatusLabel => User.StatusLabel;
    public string Status => User.Status;
    public DateTimeOffset CreatedAt => User.CreatedAt;
    public bool IsAdmin => User.IsAdmin;

    public bool IsMe { get; } = string.Equals(user.Username, currentUsername, StringComparison.Ordinal);

    public bool CanApprove => User.IsPending;
    public bool CanBan => User.IsActive && !User.IsAdmin;
    public bool CanUnban => User.IsBanned;
    public bool CanResetPassword => !IsMe;
}
