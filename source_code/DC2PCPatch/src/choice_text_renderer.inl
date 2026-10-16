// Choice-only renderer for ADV32's complete script-string entry point.
// Popup/textbox renderers and their font settings are deliberately independent.
struct ChoiceTextMask {
  std::wstring label;
  std::vector<BYTE> alpha;
  int width = 0;
  int height = 0;
  int fontHeight = 0;
  int textWidth = 0;
};

static bool NormalizeChoiceText(const std::wstring &input, std::wstring &out) {
  out.clear();
  bool gap = false;
  for (wchar_t ch : input) {
    if (ch == 0x3000 || ch == L'\t' || ch == L'\r' || ch == L'\n')
      ch = L' ';
    if (ch >= 0xFF01 && ch <= 0xFF5E)
      ch -= 0xFEE0;
    if (ch == L' ') {
      gap = !out.empty();
      continue;
    }
    if (ch < 0x20)
      return false;
    if (out.empty()) {
      if (ch != 0x25CB)
        return false;
    } else if (gap || out.size() == 1) {
      out.push_back(L' ');
    }
    out.push_back(ch);
    gap = false;
  }
  return out.size() > 2;
}

static bool BuildChoiceTextMask(const std::wstring &label, int width, int height,
                                ChoiceTextMask &out) {
  if (width < 32 || width > 800 || height < 24 || height > 96)
    return false;
  HDC dc = CreateCompatibleDC(nullptr);
  if (!dc)
    return false;
  BITMAPINFO info = {};
  info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
  info.bmiHeader.biWidth = width;
  info.bmiHeader.biHeight = -height;
  info.bmiHeader.biPlanes = 1;
  info.bmiHeader.biBitCount = 32;
  void *pixels = nullptr;
  HBITMAP bitmap = CreateDIBSection(dc, &info, DIB_RGB_COLORS, &pixels, nullptr, 0);
  if (!bitmap || !pixels) {
    if (bitmap) DeleteObject(bitmap);
    DeleteDC(dc);
    return false;
  }
  HGDIOBJ oldBitmap = SelectObject(dc, bitmap);
  HGDIOBJ oldFont = nullptr;
  HFONT font = nullptr;
  SIZE size = {};
  int fontHeight = 28;
  bool fits = false;
  for (; fontHeight >= 16; --fontHeight) {
    font = CreateFontW(-fontHeight, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                       DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                       ANTIALIASED_QUALITY, VARIABLE_PITCH | FF_SWISS, L"Arial");
    if (!font)
      break;
    oldFont = SelectObject(dc, font);
    fits = Real_GetTextExtentPoint32W(dc, label.c_str(), (int)label.size(), &size)
           && size.cx <= width - 2 && size.cy <= height - 2;
    if (fits)
      break;
    SelectObject(dc, oldFont);
    DeleteObject(font);
    font = nullptr;
  }
  bool ok = false;
  if (fits && font) {
    ZeroMemory(pixels, width * height * 4);
    SetBkMode(dc, TRANSPARENT);
    SetTextColor(dc, RGB(255, 255, 255));
    SetTextAlign(dc, TA_LEFT | TA_TOP | TA_NOUPDATECP);
    ok = Real_TextOutW(dc, 0, (height - size.cy) / 2, label.c_str(),
                       (int)label.size()) != FALSE;
    GdiFlush();
    if (ok) {
      out.label = label;
      out.width = width;
      out.height = height;
      out.fontHeight = fontHeight;
      out.textWidth = size.cx;
      out.alpha.resize(width * height);
      const BYTE *src = (const BYTE *)pixels;
      for (int i = 0; i < width * height; ++i)
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

#ifndef DC2PC_CHOICE_LAYOUT_TEST
static int (__cdecl *Real_DrawChoiceString)(int, int, int, const char *, int) = nullptr;

static void TraceChoiceLayout(const char *status, int x, int y, int flags,
                              const RECT &button, const ChoiceTextMask *mask) {
  // Explicit opt-in for verification; no normal gameplay logging.
  static int remaining = 48;
  if (remaining <= 0)
    return;
  wchar_t path[MAX_PATH] = {};
  GetModuleFileNameW(nullptr, path, MAX_PATH);
  wchar_t *name = wcsrchr(path, L'\\');
  if (!name)
    return;
  const size_t capacity = MAX_PATH - (name + 1 - path);
  wcscpy_s(name + 1, capacity, L"choice_render_trace.enabled");
  if (GetFileAttributesW(path) == INVALID_FILE_ATTRIBUTES)
    return;
  --remaining;
  wcscpy_s(name + 1, capacity, L"dc2pc_choice.log");
  FILE *file = nullptr;
  if (_wfopen_s(&file, path, L"a") == 0 && file) {
    fprintf(file, "%s x=%d y=%d flags=%X row=%ld,%ld,%ld,%ld font=%d textWidth=%d\n",
            status, x, y, flags, button.left, button.top, button.right,
            button.bottom, mask ? mask->fontHeight : 0, mask ? mask->textWidth : 0);
    fclose(file);
  }
}

static bool DecodeChoiceString(const char *text, std::wstring &label) {
  if (!text)
    return false;
  size_t length = 0;
  while (length < 2048 && IsReadablePtr(text + length, 1) && text[length])
    ++length;
  if (length < 3 || length >= 2048 || !IsReadablePtr(text + length, 1))
    return false;
  std::wstring decoded(length, L'\0');
  int n = MultiByteToWideChar(932, MB_ERR_INVALID_CHARS, text, (int)length,
                             decoded.data(), (int)decoded.size());
  if (n <= 0)
    return false;
  decoded.resize(n);
  return NormalizeChoiceText(decoded, label);
}

static bool FindChoiceButtonRect(BYTE *base, int x, int y, RECT &rect) {
  // IDA: sub_413CB0 / sub_411FF0. Each live menu row is 880 bytes;
  // offsets 12..24 hold its actual hit rectangle, independent of label length.
  const DWORD tableOffsets[] = {0x13BE00, 0x13BE04};
  const DWORD countOffsets[] = {0x7488B8, 0x722A60};
  for (int table = 0; table < 2; ++table) {
    if (!IsReadablePtr(base + tableOffsets[table], sizeof(BYTE *)) ||
        !IsReadablePtr(base + countOffsets[table], sizeof(int)))
      continue;
    const BYTE *rows = *(const BYTE **)(base + tableOffsets[table]);
    const int count = *(int *)(base + countOffsets[table]);
    if (count < 1 || count > 128 || !rows)
      continue;
    for (int i = 0; i < count; ++i) {
      const BYTE *row = rows + i * 880;
      if (!IsReadablePtr(row, 28))
        break;
      const RECT candidate = *(const RECT *)(row + 12);
      const int w = candidate.right - candidate.left;
      const int h = candidate.bottom - candidate.top;
      if (w >= 160 && w <= 800 && h >= 24 && h <= 96 &&
          x >= candidate.left - 1 && x < candidate.right &&
          y >= candidate.top - 1 && y < candidate.bottom) {
        rect = candidate;
        return true;
      }
    }
  }
  return false;
}

static bool DrawChoiceMask(BYTE *base, const ChoiceTextMask &mask,
                           const RECT &button, int flags) {
  const int index = *(const int *)(base + 0x711B80);
  if (index < 0 || index >= 35)
    return false;
  const BYTE *surface = base + 0x702AE0 + index * 0x6E0;
  if (!IsReadablePtr(surface, 20))
    return false;
  BYTE *top = *(BYTE *const *)(surface + 4);
  int stride = *(const int *)(surface + 8);
  int width = *(const int *)(surface + 12);
  int height = *(const int *)(surface + 16);
  if (!top || width <= 0 || width > 4096 || height <= 0 || height > 4096 ||
      stride < width * 3 || stride > 32768)
    return false;
  // Respect the surface's outer clip, not the temporary fixed-width text clip.
  const int l = max(max(button.left + 16, 0), *(int *)(base + 0x9EA898));
  const int t = max(max(button.top, 0), *(int *)(base + 0x9EA894));
  const int r = min(min(button.right - 16, width), *(int *)(base + 0x9EA8B0));
  const int b = min(min(button.bottom, height), *(int *)(base + 0x9EA8A8));
  if (l >= r || t >= b)
    return true;
  for (int row = t; row < b; ++row)
    if (!IsWritablePtr(top - row * stride + l * 3, (r - l) * 3))
      return false;
  const int colors[] = {(flags & 0x3F) ? 0 : 9, flags & 0x3F};
  for (int pass = (flags & 0x80) ? 0 : 1; pass < 2; ++pass) {
    const int shift = pass == 0 ? 1 : 0;
    const BYTE *rgb = base + 0x13B7B0 + colors[pass] * 4;
    for (int row = t; row < b; ++row) {
      const int sy = row - button.top - shift;
      if (sy < 0 || sy >= mask.height)
        continue;
      BYTE *dst = top - row * stride + l * 3;
      for (int col = l; col < r; ++col, dst += 3) {
        const int sx = col - button.left - 16 - shift;
        if (sx < 0 || sx >= mask.width)
          continue;
        BYTE alpha = mask.alpha[sy * mask.width + sx];
        for (int c = 0; c < 3; ++c)
          dst[c] = (BYTE)((dst[c] * (255 - alpha) + rgb[c] * alpha + 127) / 255);
      }
    }
  }
  ((void (__cdecl *)(int, int, int, int))(base + 0xBC90))(l, t, r, b);
  return true;
}

static int __cdecl Hook_DrawChoiceString(int x, int y, int lineHeight,
                                        const char *text, int flags) {
  std::wstring label;
  if (g_fontManager.GetLanguage() == 0 || !DecodeChoiceString(text, label))
    return Real_DrawChoiceString(x, y, lineHeight, text, flags);
  BYTE *base = (BYTE *)GetModuleHandleW(nullptr);
  RECT button = {};
  if (!FindChoiceButtonRect(base, x, y, button)) {
    TraceChoiceLayout("no-row", x, y, flags, button, nullptr);
    return Real_DrawChoiceString(x, y, lineHeight, text, flags);
  }
  // Cache the visible options, including their independently fitted font size.
  static std::vector<ChoiceTextMask> cache;
  ChoiceTextMask *mask = nullptr;
  const int w = button.right - button.left - 32;
  const int h = button.bottom - button.top;
  for (auto &entry : cache)
    if (entry.label == label && entry.width == w && entry.height == h)
      mask = &entry;
  if (!mask) {
    ChoiceTextMask built;
    if (!BuildChoiceTextMask(label, w, h, built)) {
      TraceChoiceLayout("no-fit", x, y, flags, button, nullptr);
      return Real_DrawChoiceString(x, y, lineHeight, text, flags);
    }
    if (cache.size() >= 32)
      cache.clear();
    cache.push_back(std::move(built));
    mask = &cache.back();
  }
  // Let the native routine keep cursor/style/byte-offset bookkeeping. Its
  // temporary empty clip suppresses only this choice's old bitmap pixels.
  int *clipRight = (int *)(base + 0x9EA8A4);
  int *clipBottom = (int *)(base + 0x9EA89C);
  const int oldRight = *clipRight, oldBottom = *clipBottom;
  *clipRight = *(int *)(base + 0x9EA8AC);
  *clipBottom = *(int *)(base + 0x9EA8A0);
  const int result = Real_DrawChoiceString(x, y, lineHeight, text, flags);
  *clipRight = oldRight;
  *clipBottom = oldBottom;
  if (!DrawChoiceMask(base, *mask, button, flags)) {
    TraceChoiceLayout("no-surface", x, y, flags, button, mask);
    return Real_DrawChoiceString(x, y, lineHeight, text, flags);
  }
  TraceChoiceLayout("rendered", x, y, flags, button, mask);
  return result;
}
#endif
