namespace DC2PCMesTextTool;

/// <summary>
/// MES script configuration for D.C.II P.C. Plus Communication.
/// </summary>
public sealed class ScriptInfo
{
    public string Name { get; init; } = "";
    public ushort Version { get; init; }

    public (byte Begin, byte End) Uint8x2 { get; init; }
    public (byte Begin, byte End) Uint8Str { get; init; }
    public (byte Begin, byte End) String { get; init; }
    public (byte Begin, byte End) EncStr { get; init; }
    public (byte Begin, byte End) Uint16x4 { get; init; }

    public byte EncryptionKey { get; init; }
    public byte[] OutputOpcodes { get; init; } = Array.Empty<byte>();

    public bool IsInSection((byte Begin, byte End) section, byte opcode)
    {
        return opcode >= section.Begin && opcode <= section.End;
    }

    public static readonly ScriptInfo DC2PC = new()
    {
        Name = "dc2pc",
        Version = 0x9969,
        Uint8x2 = (0x00, 0x28),
        Uint8Str = (0x29, 0x2E),
        String = (0x2F, 0x49),
        EncStr = (0x4A, 0x4D),
        Uint16x4 = (0x4E, 0xFF),
        EncryptionKey = 0x20,
        OutputOpcodes = new byte[] { 0x45 }
    };

    public static ScriptInfo? QueryFromData(byte[] data)
    {
        if (data.Length < 10)
            return null;

        int labelCount = BitConverter.ToInt32(data, 0);
        if (labelCount < 0 || labelCount > (data.Length - 4) / 4)
            return null;

        int bytecodeOffset = checked(labelCount * 4 + 4);
        if (bytecodeOffset + sizeof(ushort) > data.Length)
            return null;

        return BitConverter.ToUInt16(data, bytecodeOffset) == DC2PC.Version
            ? DC2PC
            : null;
    }
}
