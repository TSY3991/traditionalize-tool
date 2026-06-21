# Traditionalize Tool

[English](README.md) | [繁體中文](README.zh-TW.md)

**一個保守、安全優先的 CLI 工具，用來掃描並將檔案、資料夾、文件內容與 metadata 中的簡體中文轉換為繁體中文。**

> 先掃描、先預覽、確認後才轉換。

**作者：** TSY  
GitHub: https://github.com/TSY3991/traditionalize-tool

---

## 專案概述

Traditionalize Tool 是一個安全優先的命令列工具，適合用在專案資料夾、文件資料夾、媒體資料庫等含有中文內容的場景。

它可以掃描簡體中文，並依照使用者選擇的範圍轉換成繁體中文，例如檔名、資料夾名、純文字檔、Office 文件，以及媒體 metadata。

這個工具也適合 Codex、Claude 或其他自動化代理使用：

```text
1. 掃描目標資料夾。
2. 檢視報告。
3. 確認要修改的目標類型。
4. 執行轉換。
5. 再次掃描驗證是否仍有可轉換文字。
```

預設情況下，本工具**不翻譯其他語言**。英文、日文、韓文、套件名稱、API 名稱、路徑與程式識別字都會保留不動，除非使用者明確要求翻譯或提供自訂對照表。

---

## 可以轉換什麼

| 目標 | v0.1 支援 | 說明 |
|---|---:|---|
| 檔名與資料夾名 | 是 | 改名前會先檢查重名與非法字元。 |
| 純文字檔 | 是 | 支援 `.txt`、`.md`、`.csv`、`.json`、`.xml`、`.html`、`.yml`、`.yaml`、`.ini`、`.toml`、`.srt`、`.lrc`。 |
| Office 文件 | 是 | 支援 `.docx`、`.xlsx`、`.pptx` OOXML 文字內容。 |
| MP3 metadata | 是 | 支援 ID3v2.3/v2.4 標準文字欄位。 |
| 其他媒體 metadata | 規劃中 | MP4/M4A/FLAC/圖片 metadata 需要更安全的格式專用處理器。 |
| PDF / 圖片 OCR | 規劃中 | 會先以掃描報告為主，轉換需要額外依賴與人工確認。 |
| 程式專案 | 先掃描 | 程式碼與設定檔修改前應先人工審查。 |

---

## 安全模型

Traditionalize Tool 是刻意設計成保守工具。

- 預設模式是 `scan`，不是 `apply`。
- 不刪除檔案。
- 不移動檔案。
- 預設不翻譯非中文語言。
- 檔名轉換前會檢查重名。
- 不支援或不安全的檔案結構會列入報告，不會強制修改。
- AI 代理應先顯示掃描報告，再請使用者確認是否套用。

對程式專案來說，直接大量轉換內容可能有風險，因為文字可能出現在：

```text
README 文件
UI 文案
註解
JSON/YAML 設定
API 名稱
套件名稱
路由
lock file
產生檔
```

請先使用 scan 模式，再只對確認過的目標執行 apply。

---

## 安裝

### Windows

Windows 可以使用系統內建的轉換後端。

```bash
cd traditionalize-tool
python -m pip install -e .
```

### macOS / Linux

macOS / Linux 建議安裝 OpenCC 後端：

```bash
cd traditionalize-tool
python -m pip install -e .[opencc]
```

如果找不到 `python`，請先安裝 Python 3.10 或更新版本。

---

## 快速開始

只掃描資料夾，不修改任何檔案：

```bash
traditionalize --root "D:\Docs" --targets all --mode scan
```

只掃描檔名：

```bash
traditionalize --root "D:\Docs" --targets names --mode scan
```

檢視報告後套用檔名轉換：

```bash
traditionalize --root "D:\Docs" --targets names --mode apply
```

只掃描 Office 文件：

```bash
traditionalize --root "D:\Docs" --targets office --ext .docx,.xlsx,.pptx --mode scan
```

給 Codex、Claude、CI 或其他自動化工具使用 JSON 輸出：

```bash
traditionalize --root ./project --targets text --mode scan --json
```

---

## CLI 參數

```text
--root      必填。要掃描的檔案或資料夾根路徑。
--targets   逗號分隔的目標：scan,names,text,office,media,all。
--mode      scan 或 apply。預設為 scan。
--ext       可選，逗號分隔的副檔名白名單。
--json      輸出機器可讀的 JSON。
```

範例：

```bash
traditionalize --root ./docs --targets text --mode scan
traditionalize --root ./docs --targets text --ext .md,.txt --mode apply
traditionalize --root ./media --targets media --mode scan --json
```

---

## AI 代理使用方式

本專案設計成容易被 AI coding agent 呼叫。

建議流程：

```text
Step 1: 執行 scan 模式。
Step 2: 摘要檔案數量與修改範例。
Step 3: 請使用者確認要修改的目標。
Step 4: 只對確認過的目標執行 apply。
Step 5: 再次執行 scan 驗證。
```

Claude 使用說明：

```text
CLAUDE.md
```

Codex skill 可以放在：

```text
~/.codex/skills/convert-to-traditional-chinese
```

Claude skill 可以放在：

```text
~/.claude/skills/convert-to-traditional-chinese
```

---

## 目前限制

- 第一版專注於簡體中文轉繁體中文，不做翻譯。
- macOS / Linux 需要 OpenCC 才能轉換。
- Office 支援 OOXML 格式：`.docx`、`.xlsx`、`.pptx`。
- 舊版 Office 格式 `.doc`、`.xls`、`.ppt` 尚未支援。
- PDF、OCR、MP4/M4A/FLAC metadata、圖片 metadata 尚未預設啟用。
- 程式專案內容轉換前應先人工審查。

---

## Roadmap

- 增加明確的 OpenCC 後端選擇。
- 增加 dry-run diff 輸出。
- 增加備份 / 還原選項。
- 增加更安全的 JSON/YAML key/value 定位。
- 增加 MP4/M4A/FLAC metadata 處理器。
- 增加 PDF metadata 掃描模式。
- 增加 Markdown/JSON 報告匯出。
- 增加測試資料與 fixtures。
- 增加 GitHub Actions CI。

---

## FAQ

**Q: 這會把英文或日文翻譯成繁體中文嗎？**  
A: 不會。預設目標是簡體中文轉繁體中文。翻譯是另一個功能，必須使用者明確確認。

**Q: 可以用在程式專案嗎？**  
A: 可以，但請先掃描。直接套用到原始碼或設定檔可能會改到識別字、路由或外部 API 名稱。

**Q: 會修改音訊或影片內容嗎？**  
A: 不會。MP3 支援只處理 ID3 文字 metadata。

**Q: 為什麼一定要先掃描？**  
A: 因為檔名重名、不支援格式、專案特殊文字都可能造成非預期修改。工具的設計目標是先讓風險可見。

---

## License

License 尚未決定。正式公開穩定版前，請加入 `LICENSE` 檔案。

MIT 或 Apache-2.0 都是這類 CLI 工具常見的選擇。

---

## Contributing

初版公開後歡迎 issue 與 pull request。

建議貢獻方向：

- 更多檔案格式處理器
- 更安全的專案感知轉換規則
- 測試資料與 fixtures
- 跨平台轉換後端
- 文件改善

---

**如果這個工具對你的文件或媒體整理流程有幫助，歡迎 Star 或 Fork。**
