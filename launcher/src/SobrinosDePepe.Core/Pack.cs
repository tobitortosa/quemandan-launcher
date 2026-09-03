using System.Text.Json;
using System.Text.Json.Serialization;

namespace SobrinosDePepe.Core;

/// <summary>
/// El pack: qué versión de Minecraft, qué loader de Fabric y qué mods exactos.
/// En la fase 0 se lee de un archivo local; después lo sirve el backend en /api/pack.
/// </summary>
public sealed class Pack
{
    [JsonPropertyName("packVersion")] public string PackVersion { get; set; } = "0.0.0";
    [JsonPropertyName("minecraft")] public string Minecraft { get; set; } = "";
    [JsonPropertyName("fabricLoader")] public string FabricLoader { get; set; } = "";
    [JsonPropertyName("server")] public PackServer Server { get; set; } = new();
    [JsonPropertyName("mods")] public List<PackMod> Mods { get; set; } = [];

    /// <summary>Los mods que van al cliente. Los de solo servidor no se descargan acá.</summary>
    public IEnumerable<PackMod> ClientMods =>
        Mods.Where(m => m.Side is "client" or "both");

    public static Pack Load(string path)
    {
        var json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<Pack>(json)
            ?? throw new InvalidDataException($"No se pudo leer el pack: {path}");
    }
}

public sealed class PackServer
{
    [JsonPropertyName("name")] public string Name { get; set; } = "";
    [JsonPropertyName("address")] public string Address { get; set; } = "";
}

public sealed class PackMod
{
    [JsonPropertyName("projectId")] public string ProjectId { get; set; } = "";
    [JsonPropertyName("slug")] public string Slug { get; set; } = "";
    [JsonPropertyName("title")] public string Title { get; set; } = "";
    [JsonPropertyName("versionId")] public string VersionId { get; set; } = "";
    [JsonPropertyName("versionNumber")] public string VersionNumber { get; set; } = "";
    [JsonPropertyName("filename")] public string Filename { get; set; } = "";
    [JsonPropertyName("url")] public string Url { get; set; } = "";
    [JsonPropertyName("sha1")] public string Sha1 { get; set; } = "";
    [JsonPropertyName("sha512")] public string Sha512 { get; set; } = "";
    [JsonPropertyName("size")] public long Size { get; set; }

    /// <summary>"client", "server" o "both".</summary>
    [JsonPropertyName("side")] public string Side { get; set; } = "both";

    [JsonPropertyName("license")] public string License { get; set; } = "";
    [JsonPropertyName("pageUrl")] public string PageUrl { get; set; } = "";
    [JsonPropertyName("requires")] public List<string> Requires { get; set; } = [];
}
