using System.Globalization;
using Avalonia.Data.Converters;
using Avalonia.Media;

namespace QueMandan.App;

/// <summary>Verde si el servidor responde, rojo si no.</summary>
public sealed class StatusColorConverter : IValueConverter
{
    public static readonly StatusColorConverter Instance = new();

    public object Convert(object? value, Type targetType, object? parameter, CultureInfo culture) =>
        value is true ? Color.Parse("#4ADE80") : Color.Parse("#F87171");

    public object ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture) =>
        throw new NotSupportedException();
}

/// <summary>El color del estado de una cuenta: pendiente, activa o baneada.</summary>
public sealed class AccountStatusColorConverter : IValueConverter
{
    public static readonly AccountStatusColorConverter Instance = new();

    public object Convert(object? value, Type targetType, object? parameter, CultureInfo culture) =>
        new SolidColorBrush((value as string) switch
        {
            "pending" => Color.Parse("#F5A524"),
            "active" => Color.Parse("#4ADE80"),
            "banned" => Color.Parse("#F87171"),
            _ => Color.Parse("#9AA0AA"),
        });

    public object ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture) =>
        throw new NotSupportedException();
}
