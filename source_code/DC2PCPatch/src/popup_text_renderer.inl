// ADV32's 28px bitmap-string renderer is separate from HSXF4/GDI text.
// Replace complete confirmation labels here, before the fixed-width loop.
static void (__cdecl *Real_DrawBitmapText28)(int, int, const char *, int) = nullptr;
static int (__cdecl *Real_DrawScriptGlyph)(const char *, int, int) = nullptr;
static thread_local bool g_suppressPopupBitmapGlyph = false;

struct PopupTextMask {
  std::wstring text;
  std::vector<BYTE> alpha;
  int width = 0;
  int height = 0;
};

static bool DecodePopupLabel(const char *text, std::wstring &label) {
  if (!text)
    return false;
  size_t len = 0;
  while (len < 160 && IsReadablePtr(text + len, 1) && text[len])
    ++len;
  if (len < 5 || len >= 160 || !IsReadablePtr(text + len, 1))
    return false;
  wchar_t wide[161] = {};
  int count = MultiByteToWideChar(932, MB_ERR_INVALID_CHARS, text, (int)len,
                                wide, 160);
  if (count <= 0)
    return false;
  label.assign(wide, count);
  std::string match;
  for (wchar_t &ch : label) {
    if (ch == 0x3000 || ch == L'\t')
      ch = L' ';
    else if (ch >= 0xFF01 && ch <= 0xFF5E)
      ch -= 0xFEE0;
    if (ch < 0x20 || ch > 0x7E)
      return false;
    match.push_back((char)tolower((unsigned char)ch));
  }
  // The label itself is always taken from the MES imported from JSON.
  return match == "muat permainan?" || match == "simpan disini?" ||
         match == "simpan di sini?" || match == "reset config?" ||
         match == "mau kembali?" || match == "ingin keluar?";
}

static bool BuildPopupTextMask(const std::wstring &label, PopupTextMask &out) {
  constexpr int canvasW = 224, canvasH = 64;
  HDC dc = CreateCompatibleDC(nullptr);
  if (!dc)
    return false;
  BITMAPINFO info = {};
  info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
  info.bmiHeader.biWidth = canvasW;
  info.bmiHeader.biHeight = -canvasH;
  info.bmiHeader.biPlanes = 1;
  info.bmiHeader.biBitCount = 32;
  info.bmiHeader.biCompression = BI_RGB;
  void *pixels = nullptr;
  HBITMAP bitmap = CreateDIBSection(dc, &info, DIB_RGB_COLORS, &pixels, nullptr, 0);
  if (!bitmap || !pixels) {
    if (bitmap) DeleteObject(bitmap);
    DeleteDC(dc);
    return false;
  }
  HGDIOBJ oldBitmap = SelectObject(dc, bitmap);
  HFONT font = nullptr;
  HGDIOBJ oldFont = nullptr;
  SIZE size = {};
  bool fits = false;
  for (int height = 30; height >= 18; --height) {
    font = CreateFontW(-height, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                       ANSI_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                       ANTIALIASED_QUALITY, VARIABLE_PITCH | FF_SWISS, L"Arial");
    if (!font)
      break;
    oldFont = SelectObject(dc, font);
    fits = Real_GetTextExtentPoint32W(dc, label.c_str(), (int)label.size(), &size)
           && size.cx <= canvasW - 8 && size.cy <= canvasH;
    if (fits)
      break;
    SelectObject(dc, oldFont);
    DeleteObject(font);
    font = nullptr;
  }
  bool ok = false;
  if (fits && font) {
    ZeroMemory(pixels, canvasW * canvasH * 4);
    SetBkMode(dc, TRANSPARENT);
    SetTextColor(dc, RGB(255, 255, 255));
    SetTextAlign(dc, TA_LEFT | TA_TOP | TA_NOUPDATECP);
    ok = Real_TextOutW(dc, (canvasW - size.cx) / 2,
                       (canvasH - size.cy) / 2, label.c_str(), (int)label.size()) != FALSE;
    GdiFlush();
    if (ok) {
      out.text = label;
      out.width = canvasW;
      out.height = canvasH;
      out.alpha.resize(canvasW * canvasH);
      const BYTE *src = (const BYTE *)pixels;
      for (int i = 0; i < canvasW * canvasH; ++i)
        out.alpha[i] = src[i * 4];
    }
  }
  if (font) {
    SelectObject(dc, oldFont);
    DeleteObject(font);
  }
  SelectObject(dc, oldBitmap);
  DeleteObject(bitmap);
  DeleteDC(dc);
  return ok;
}

static bool DrawProportionalPopupLabel(int x, int y, const char *text, int color) {
  if (g_fontManager.GetLanguage() == 0 || x < 260 || x > 540 || y < 235 || y > 315)
    return false;
  std::wstring label;
  if (!DecodePopupLabel(text, label))
    return false;
  static PopupTextMask mask;
  if (mask.text != label && !BuildPopupTextMask(label, mask))
    return false;

  BYTE *base = (BYTE *)GetModuleHandleW(nullptr);
  const int *targetIndex = (const int *)(base + 0x711B80);
  if (!IsReadablePtr(targetIndex, sizeof(int)) || *targetIndex < 0 || *targetIndex >= 35)
    return false;
  // Native surface records: top scanline pointer, positive bottom-up stride,
  // width and height. Match the addressing used by ADV32's own bitmap blitter.
  const BYTE *surface = base + 0x702AE0 + *targetIndex * 0x6E0;
  if (!IsReadablePtr(surface, 20))
    return false;
  BYTE *top = *(BYTE *const *)(surface + 4);
  int stride = *(const int *)(surface + 8);
  int width = *(const int *)(surface + 12);
  int height = *(const int *)(surface + 16);
  if (!top || width < 520 || width > 4096 || height < 312 || height > 4096 ||
      stride < width * 3 || stride > 32768 || color < 0 || color >= 64)
    return false;
  const int *clipLeft = (const int *)(base + 0x9EA8AC);
  const int *clipTop = (const int *)(base + 0x9EA8A0);
  const int *clipRight = (const int *)(base + 0x9EA8A4);
  const int *clipBottom = (const int *)(base + 0x9EA89C);
  int left = 288, topY = 246, right = left + mask.width, bottom = topY + mask.height;
  int l = left > *clipLeft ? left : *clipLeft;
  int t = topY > *clipTop ? topY : *clipTop;
  int r = right < *clipRight ? right : *clipRight;
  int b = bottom < *clipBottom ? bottom : *clipBottom;
  if (l < 0) l = 0;
  if (t < 0) t = 0;
  if (r > width) r = width;
  if (b > height) b = height;
  if (l >= r || t >= b)
    return true;
  for (int row = t; row < b; ++row)
    if (!IsWritablePtr(top - row * stride + l * 3, (r - l) * 3))
      return false;
  const BYTE *rgb = base + 0x13B7B0 + color * 4;
  for (int row = t; row < b; ++row) {
    BYTE *dst = top - row * stride + l * 3;
    const BYTE *alpha = mask.alpha.data() + (row - topY) * mask.width + l - left;
    for (int col = l; col < r; ++col, dst += 3, ++alpha) {
      for (int channel = 0; channel < 3; ++channel)
        dst[channel] = (BYTE)((dst[channel] * (255 - *alpha) + rgb[channel] * *alpha + 127) / 255);
    }
  }
  typedef void (__cdecl *DirtyRectProc)(int, int, int, int);
  ((DirtyRectProc)(base + 0xBC90))(l, t, r, b);
  return true;
}

static void __cdecl Hook_DrawBitmapText28(int x, int y, const char *text, int color) {
  if (g_suppressPopupBitmapGlyph)
    return;
  if (!DrawProportionalPopupLabel(x, y, text, color))
    Real_DrawBitmapText28(x, y, text, color);
}

// This script renderer receives the complete decoded MES string plus a byte
// offset, then passes a temporary single-glyph string to the bitmap renderer.
// Keep its cursor, style and script bookkeeping; only replace the bitmap draw.
static int __cdecl Hook_DrawScriptGlyph(const char *text, int offset, int flags) {
  BYTE *base = (BYTE *)GetModuleHandleW(nullptr);
  int x = *(int *)(base + 0x7D590C);
  int y = *(int *)(base + 0x753134);
  static thread_local const char *runText = nullptr;
  static thread_local bool replaced = false;
  std::wstring label;
  bool popup = g_fontManager.GetLanguage() != 0 && x >= 260 && x <= 540 &&
               y >= 235 && y <= 315 && DecodePopupLabel(text, label);
  if (offset == 0) {
    runText = text;
    replaced = popup && DrawProportionalPopupLabel(x, y, text, flags & 0x3F);
  }
  bool previous = g_suppressPopupBitmapGlyph;
  g_suppressPopupBitmapGlyph = popup && runText == text && replaced;
  int result = Real_DrawScriptGlyph(text, offset, flags);
  g_suppressPopupBitmapGlyph = previous;
  return result;
}
