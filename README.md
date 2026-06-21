# Traditionalize Tool

[English](README.md) | [繁體中文](README.zh-TW.md)

**A conservative CLI for turning Simplified Chinese into Traditional Chinese across files, folders, documents, and metadata.**

> Scan first. Preview changes. Convert only what you confirm.

**Author:** TSY  
GitHub: https://github.com/TSY3991/traditionalize-tool

---

## Overview

Traditionalize Tool is a safety-first command line utility for projects, document folders, and media libraries that contain mixed Chinese text.

It can scan for Simplified Chinese and convert it to Traditional Chinese in selected targets such as filenames, folder names, plain text files, Office documents, and media metadata.

The tool is designed for both humans and AI agents such as Codex or Claude:

```text
1. Scan the target folder.
2. Review the report.
3. Confirm the exact target types to modify.
4. Apply changes.
5. Verify that no convertible Simplified Chinese remains.
```

It does **not** translate other languages by default. English, Japanese, Korean, package names, API names, paths, and code identifiers are left unchanged unless a user explicitly asks for translation or custom mapping.

---

## What It Can Convert

| Target | Supported in v0.1 | Notes |
|---|---:|---|
| File and folder names | Yes | Preflights collisions and invalid filename characters before renaming. |
| Plain text files | Yes | Supports `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.html`, `.yml`, `.yaml`, `.ini`, `.toml`, `.srt`, `.lrc`. |
| Office documents | Yes | Supports `.docx`, `.xlsx`, `.pptx` OOXML package text. |
| MP3 metadata | Yes | Supports ID3v2.3/v2.4 standard text frames. |
| Other media metadata | Planned | MP4/M4A/FLAC/image metadata require safer format-specific handlers. |
| PDF/image OCR | Planned | Scan/report first; conversion requires extra dependencies and review. |
| Source code projects | Scan-first | Code/config changes should be reviewed carefully before apply. |

---

## Safety Model

Traditionalize Tool is intentionally conservative.

- Default mode is `scan`, not `apply`.
- It never deletes files.
- It never moves files.
- It does not translate non-Chinese languages by default.
- Filename conversion checks for collisions before renaming.
- Unsupported or unsafe file structures are reported instead of forced.
- Agent workflows should always show the scan report before applying changes.

For software projects, broad content conversion can be risky because text may appear in:

```text
README files
UI strings
comments
JSON/YAML config
API names
package names
routes
lock files
generated files
```

Use scan mode first and apply only to confirmed targets.

---

## Installation

### Windows

Windows can use the built-in system conversion backend.

```bash
cd traditionalize-tool
python -m pip install -e .
```

### macOS / Linux

Install with the OpenCC backend:

```bash
cd traditionalize-tool
python -m pip install -e .[opencc]
```

If `python` is not found, install Python 3.10 or newer first.

---

## Quick Start

Scan a folder without modifying anything:

```bash
traditionalize --root "D:\Docs" --targets all --mode scan
```

Scan filenames only:

```bash
traditionalize --root "D:\Docs" --targets names --mode scan
```

Apply filename conversion after reviewing the scan report:

```bash
traditionalize --root "D:\Docs" --targets names --mode apply
```

Scan Office documents only:

```bash
traditionalize --root "D:\Docs" --targets office --ext .docx,.xlsx,.pptx --mode scan
```

Use JSON output for Codex, Claude, CI, or other automation:

```bash
traditionalize --root ./project --targets text --mode scan --json
```

---

## CLI Options

```text
--root      Required. File or folder root to scan.
--targets   Comma-separated targets: scan,names,text,office,media,all.
--mode      scan or apply. Defaults to scan.
--ext       Optional comma-separated extension allowlist.
--json      Emit machine-readable JSON output.
```

Examples:

```bash
traditionalize --root ./docs --targets text --mode scan
traditionalize --root ./docs --targets text --ext .md,.txt --mode apply
traditionalize --root ./media --targets media --mode scan --json
```

---

## Agent Usage

This project is intended to be easy for AI coding agents to call.

Recommended agent flow:

```text
Step 1: Run scan mode.
Step 2: Summarize the number of files and examples of changes.
Step 3: Ask the user to confirm exact targets.
Step 4: Run apply mode only for confirmed targets.
Step 5: Run scan mode again to verify.
```

Claude-specific guidance is in:

```text
CLAUDE.md
```

Codex skill guidance can live in:

```text
~/.codex/skills/convert-to-traditional-chinese
```

Claude skill guidance can live in:

```text
~/.claude/skills/convert-to-traditional-chinese
```

---

## Current Limitations

- The first version focuses on Simplified-to-Traditional conversion, not translation.
- macOS/Linux require OpenCC for conversion.
- Office support works on OOXML formats: `.docx`, `.xlsx`, `.pptx`.
- Legacy Office formats such as `.doc`, `.xls`, `.ppt` are not supported yet.
- PDF, OCR, MP4/M4A/FLAC metadata, and image metadata are planned but not enabled by default.
- Code project conversion should be reviewed manually before apply.

---

## Roadmap

- Add first-class OpenCC backend selection.
- Add dry-run diff output.
- Add backup/restore option.
- Add safer JSON/YAML key/value targeting.
- Add MP4/M4A/FLAC metadata handlers.
- Add PDF metadata scan mode.
- Add report export to Markdown/JSON.
- Add tests and sample fixtures.
- Add GitHub Actions CI.

---

## FAQ

**Q: Does this translate English or Japanese into Traditional Chinese?**  
A: No. The default goal is Simplified Chinese to Traditional Chinese. Translation is a separate feature and should require explicit confirmation.

**Q: Can I run this on a software project?**  
A: Yes, but scan first. Applying conversion to source code or config files can change identifiers, routes, or external API names if used carelessly.

**Q: Does it modify audio/video content?**  
A: No. MP3 support targets ID3 text metadata only.

**Q: Why scan before apply?**  
A: Because filename collisions, unsupported formats, and project-specific text can create unwanted changes. The tool is designed to make those risks visible first.

---

## License

License has not been finalized yet. Add a `LICENSE` file before publishing a stable release.

MIT or Apache-2.0 are good default options for this type of CLI tool.

---

## Contributing

Issues and pull requests are welcome after the initial public release.

Recommended contribution areas:

- Additional file format handlers
- Safer project-aware conversion rules
- Test fixtures
- Cross-platform conversion backends
- Documentation improvements

---

**If this tool helps your document or media cleanup workflow, consider starring or forking the project.**

