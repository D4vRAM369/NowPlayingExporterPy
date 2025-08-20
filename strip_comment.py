#!/usr/bin/env python3
import re, sys, shutil, os
from pathlib import Path

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("src")
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("clean-src")

EXCLUDE_DIRS = {".git", "build", ".gradle", ".idea", "__pycache__", "venv", ".venv", "tmp", "temp"}

KT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.S)
XML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)

def strip_line_comment_kt(line: str) -> str:
    # Quita // fuera de literales de cadena
    res = []
    in_str = False
    escape = False
    i = 0
    while i < len(line):
        ch = line[i]
        if in_str:
            res.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        else:
            if ch == '"':
                in_str = True
                res.append(ch)
                i += 1
                continue
            if ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                break  # corta aquí
            res.append(ch)
            i += 1
    return "".join(res).rstrip()

def process_text(p: Path, text: str) -> str:
    if p.suffix in [".kt", ".java"]:
        text = KT_BLOCK_RE.sub("", text)
        out = []
        for line in text.splitlines():
            out.append(strip_line_comment_kt(line))
        return "\n".join(out).strip() + "\n"
    elif p.suffix == ".xml":
        return XML_COMMENT_RE.sub("", text)
    elif p.suffix == ".py":
        out = []
        for line in text.splitlines():
            if line.lstrip().startswith("#"):
                continue
            out.append(line)
        return "\n".join(out).strip() + "\n"
    else:
        return text

def should_copy_dir(d: Path) -> bool:
    return d.name not in EXCLUDE_DIRS

def main():
    if DST.exists():
        shutil.rmtree(DST)
    for root, dirs, files in os.walk(SRC):
        root_p = Path(root)
        dirs[:] = [d for d in dirs if should_copy_dir(Path(d))]
        rel = root_p.relative_to(SRC)
        (DST / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            src_f = root_p / f
            dst_f = DST / rel / f
            try:
                if src_f.suffix in [".kt", ".java", ".xml", ".py"]:
                    txt = src_f.read_text(encoding="utf-8", errors="ignore")
                    cleaned = process_text(src_f, txt)
                    dst_f.write_text(cleaned, encoding="utf-8")
                else:
                    shutil.copy2(src_f, dst_f)
            except Exception as e:
                print(f"[WARN] No se pudo procesar {src_f}: {e}")
    print(f"✓ Código limpio generado en: {DST}")

if __name__ == "__main__":
    main()

