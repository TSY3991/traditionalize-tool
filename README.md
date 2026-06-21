# traditionalize-tool

A conservative CLI for scanning and converting Simplified Chinese to Traditional Chinese across filenames, folder names, plain text files, Office Open XML documents, and MP3 ID3 metadata.

The tool is designed for agent workflows too: Codex, Claude, or any automation should run `scan` first, show the report, then run `apply` only after user confirmation.

## Install

```bash
python -m pip install -e .
```

For non-Windows computers, install the OpenCC extra:

```bash
python -m pip install -e .[opencc]
```

Windows can use the built-in NLS conversion backend. OpenCC can also be installed on Windows for more consistent behavior across platforms.

## Usage

Scan first:

```bash
traditionalize --root "D:\\Docs" --targets names,text,office,media --mode scan
```

Apply after confirmation:

```bash
traditionalize --root "D:\\Docs" --targets names --mode apply
```

Use JSON output for agents:

```bash
traditionalize --root ./project --targets text --mode scan --json
```

## Targets

- `names`: file and folder names
- `text`: plain text-like files such as `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.html`, `.yml`
- `office`: `.docx`, `.xlsx`, `.pptx` OOXML package text
- `media`: `.mp3` ID3v2.3/v2.4 text frames
- `all`: all supported targets

## Safety

- Never deletes files.
- Never moves files.
- Runs in scan mode by default.
- Checks filename collisions before rename apply.
- Does not translate non-Chinese languages by default.
- Stops on unsupported or unsafe metadata/document structures.

## License

Choose and add a license before publishing. MIT or Apache-2.0 are common choices for CLI tools.
