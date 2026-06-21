from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

TEXT_EXTS = {
    ".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm",
    ".yml", ".yaml", ".ini", ".toml", ".srt", ".lrc",
}
OFFICE_EXTS = {".docx", ".xlsx", ".pptx"}
INVALID_NAME_CHARS = set('<>:"/\\|?*')


@dataclass
class Change:
    target: str
    path: str
    detail: str
    old: str
    new: str


@dataclass
class Report:
    root: str
    mode: str
    targets: list[str]
    scanned_files: int = 0
    changes: list[Change] | None = None
    errors: list[str] | None = None
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        self.changes = [] if self.changes is None else self.changes
        self.errors = [] if self.errors is None else self.errors
        self.warnings = [] if self.warnings is None else self.warnings


def to_traditional(text: str) -> str:
    if not text:
        return text
    try:
        from opencc import OpenCC  # type: ignore
        if not hasattr(to_traditional, "_opencc"):
            to_traditional._opencc = OpenCC("s2t")  # type: ignore[attr-defined]
        return to_traditional._opencc.convert(text)  # type: ignore[attr-defined]
    except ImportError:
        pass
    if os.name == "nt":
        return windows_to_traditional(text)
    raise RuntimeError("No conversion backend available. Install with: pip install .[opencc]")


def windows_to_traditional(text: str) -> str:
    flag = 0x04000000
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    fn = kernel32.LCMapStringEx
    fn.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    fn.restype = ctypes.c_int
    n = fn("zh-TW", flag, text, len(text), None, 0, None, None, None)
    if n == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    buf = ctypes.create_unicode_buffer(n)
    r = fn("zh-TW", flag, text, len(text), buf, n, None, None, None)
    if r == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return buf.value[:r]


def safe_decode(data: bytes) -> tuple[str, str] | None:
    for enc in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "big5"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return None


def preview(text: str, limit: int = 120) -> str:
    compact = text.replace("\r", " ").replace("\n", " ")
    return compact[:limit] + ("..." if len(compact) > limit else "")


def scan_names(root: Path, report: Report, apply: bool) -> None:
    items = sorted(root.rglob("*"), key=lambda p: len(str(p)), reverse=True)
    planned: list[tuple[Path, str]] = []
    final_names: dict[Path, list[str]] = {}
    for item in items:
        new_name = to_traditional(item.name)
        key_name = new_name.lower() if os.name == "nt" else new_name
        final_names.setdefault(item.parent, []).append(key_name)
        if new_name != item.name:
            if any(ch in INVALID_NAME_CHARS for ch in new_name):
                report.errors.append(f"Invalid target filename: {item} -> {new_name}")
            planned.append((item, new_name))
            report.changes.append(Change("names", str(item), "rename", item.name, new_name))
    for parent, names in final_names.items():
        if len(names) != len(set(names)):
            report.errors.append(f"Filename collision under {parent}")
    if apply and not report.errors:
        for item, new_name in planned:
            if item.exists():
                item.rename(item.with_name(new_name))


def scan_text(root: Path, report: Report, apply: bool, exts: set[str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        report.scanned_files += 1
        try:
            decoded = safe_decode(path.read_bytes())
            if decoded is None:
                report.warnings.append(f"Skip undecodable text file: {path}")
                continue
            text, enc = decoded
            new = to_traditional(text)
            if new != text:
                report.changes.append(Change("text", str(path), enc, preview(text), preview(new)))
                if apply:
                    path.write_bytes(new.encode(enc))
        except Exception as exc:
            report.errors.append(f"Text error {path}: {exc}")


def scan_office(root: Path, report: Report, apply: bool, exts: set[str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        report.scanned_files += 1
        try:
            replacements: dict[str, bytes] = {}
            with zipfile.ZipFile(path, "r") as zin:
                for info in zin.infolist():
                    if not info.filename.lower().endswith(".xml"):
                        continue
                    data = zin.read(info.filename)
                    try:
                        new_data, changed = convert_xml_bytes(data)
                    except ET.ParseError:
                        continue
                    if changed:
                        replacements[info.filename] = new_data
                        report.changes.append(Change("office", str(path), info.filename, "XML text", "Traditionalized XML text"))
            if apply and replacements:
                rewrite_zip(path, replacements)
        except Exception as exc:
            report.errors.append(f"Office error {path}: {exc}")


def convert_xml_bytes(data: bytes) -> tuple[bytes, bool]:
    root = ET.fromstring(data)
    changed = False
    for elem in root.iter():
        if elem.text:
            new = to_traditional(elem.text)
            if new != elem.text:
                elem.text = new
                changed = True
        if elem.tail:
            new = to_traditional(elem.tail)
            if new != elem.tail:
                elem.tail = new
                changed = True
        for key, value in list(elem.attrib.items()):
            new = to_traditional(value)
            if new != value:
                elem.attrib[key] = new
                changed = True
    if not changed:
        return data, False
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), True


def rewrite_zip(path: Path, replacements: dict[str, bytes]) -> None:
    fd, tmp_name = tempfile.mkstemp(suffix=path.suffix)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                zout.writestr(info, replacements.get(info.filename, zin.read(info.filename)))
        shutil.move(str(tmp), str(path))
    finally:
        if tmp.exists():
            tmp.unlink()


def read_syncsafe(b: bytes, o: int) -> int:
    return ((b[o] & 0x7F) << 21) | ((b[o + 1] & 0x7F) << 14) | ((b[o + 2] & 0x7F) << 7) | (b[o + 3] & 0x7F)


def read_u32be(b: bytes, o: int) -> int:
    return (b[o] << 24) | (b[o + 1] << 16) | (b[o + 2] << 8) | b[o + 3]


def write_syncsafe(n: int) -> bytes:
    return bytes([(n >> 21) & 0x7F, (n >> 14) & 0x7F, (n >> 7) & 0x7F, n & 0x7F])


def write_u32be(n: int) -> bytes:
    return bytes([(n >> 24) & 255, (n >> 16) & 255, (n >> 8) & 255, n & 255])


def decode_id3_text(payload: bytes) -> str:
    if not payload:
        return ""
    enc = payload[0]
    data = payload[1:]
    if enc == 0:
        return data.decode("latin-1").rstrip("\x00")
    if enc == 1:
        return (data.decode("utf-16") if data.startswith((b"\xff\xfe", b"\xfe\xff")) else data.decode("utf-16-le")).lstrip("\ufeff").rstrip("\x00")
    if enc == 2:
        if data.startswith(b"\xfe\xff"):
            data = data[2:]
        return data.decode("utf-16-be").lstrip("\ufeff").rstrip("\x00")
    if enc == 3:
        return data.decode("utf-8").rstrip("\x00")
    raise ValueError(f"Unsupported ID3 text encoding {enc}")


def encode_id3_text(enc: int, text: str) -> bytes:
    if enc == 0:
        body = text.encode("latin-1")
    elif enc == 1:
        body = b"\xff\xfe" + text.encode("utf-16-le")
    elif enc == 2:
        body = b"\xfe\xff" + text.encode("utf-16-be")
    elif enc == 3:
        body = text.encode("utf-8")
    else:
        raise ValueError(f"Unsupported ID3 text encoding {enc}")
    return bytes([enc]) + body


def scan_media(root: Path, report: Report, apply: bool) -> None:
    for path in root.rglob("*.mp3"):
        report.scanned_files += 1
        try:
            changes = convert_mp3_id3(path, apply)
            for frame, old, new in changes:
                report.changes.append(Change("media", str(path), frame, old, new))
        except Exception as exc:
            report.errors.append(f"MP3 metadata error {path}: {exc}")


def convert_mp3_id3(path: Path, apply: bool) -> list[tuple[str, str, str]]:
    b = path.read_bytes()
    if len(b) < 10 or b[:3] != b"ID3":
        return []
    major = b[3]
    if major not in (3, 4):
        raise ValueError(f"Unsupported ID3v2.{major}")
    if b[5] & 0x40:
        raise ValueError("Extended ID3 header not supported in first version")
    tag_size = read_syncsafe(b, 6)
    tag_end = 10 + tag_size
    out = bytearray()
    pos = 10
    changes: list[tuple[str, str, str]] = []
    while pos + 10 <= tag_end:
        fid = b[pos:pos + 4].decode("ascii", errors="replace")
        if fid == "\x00\x00\x00\x00" or not re.fullmatch(r"[A-Z0-9]{4}", fid):
            break
        size = read_syncsafe(b, pos + 4) if major == 4 else read_u32be(b, pos + 4)
        if size <= 0 or pos + 10 + size > tag_end:
            raise ValueError(f"Invalid frame {fid}")
        flags = b[pos + 8:pos + 10]
        payload = b[pos + 10:pos + 10 + size]
        if fid.startswith("T") and fid != "TXXX":
            old = decode_id3_text(payload)
            new = to_traditional(old)
            if old != new:
                changes.append((fid, old, new))
                payload = encode_id3_text(payload[0], new)
        out += fid.encode("ascii")
        out += write_syncsafe(len(payload)) if major == 4 else write_u32be(len(payload))
        out += flags + payload
        pos += 10 + size
    if apply and changes:
        out += b"\x00" * 1024
        nb = bytearray(b[:10])
        nb[6:10] = write_syncsafe(len(out))
        nb += out
        nb += b[tag_end:]
        path.write_bytes(nb)
    return changes


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scan/apply Simplified-to-Traditional Chinese conversion.")
    p.add_argument("--root", required=True)
    p.add_argument("--targets", default="scan", help="Comma-separated: scan,names,text,office,media,all")
    p.add_argument("--mode", choices=("scan", "apply"), default="scan")
    p.add_argument("--ext", default="", help="Comma-separated extension allowlist, e.g. .docx,.xlsx")
    p.add_argument("--json", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Root does not exist: {root}", file=sys.stderr)
        return 2
    targets = [t.strip().lower() for t in args.targets.split(",") if t.strip()]
    if "all" in targets or targets == ["scan"]:
        targets = ["names", "text", "office", "media"]
    exts = {e.strip().lower() for e in args.ext.split(",") if e.strip()}
    report = Report(str(root), args.mode, targets)
    apply = args.mode == "apply"
    if "names" in targets:
        scan_names(root, report, apply)
    if "text" in targets:
        scan_text(root, report, apply, exts or TEXT_EXTS)
    if "office" in targets:
        scan_office(root, report, apply, exts or OFFICE_EXTS)
    if "media" in targets:
        scan_media(root, report, apply)
    data = asdict(report)
    data["change_count"] = len(report.changes or [])
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"Root: {report.root}")
        print(f"Mode: {report.mode}")
        print(f"Targets: {', '.join(report.targets)}")
        print(f"Scanned files: {report.scanned_files}")
        print(f"Changes: {len(report.changes or [])}")
        print(f"Errors: {len(report.errors or [])}")
        print(f"Warnings: {len(report.warnings or [])}")
        for change in (report.changes or [])[:20]:
            print(f"- [{change.target}] {change.path} :: {change.detail}: {change.old} -> {change.new}")
        for err in (report.errors or [])[:20]:
            print(f"ERROR: {err}", file=sys.stderr)
        for warn in (report.warnings or [])[:20]:
            print(f"WARN: {warn}", file=sys.stderr)
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
