# -*- coding: utf-8 -*-
import csv, re
from datetime import datetime, timezone, timedelta

def _norm(s):
    if s is None: return ""
    s = str(s).lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _parse_iso(ts):
    if not ts: return None
    ts = ts.strip()
    if not ts: return None
    if ts.endswith("Z"):
        ts = ts[:-1]
        try:
            return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def _split_display(display):
    if not display: return ("","")
    parts = re.split(r"\s+[-—–]\s+", str(display), maxsplit=1)
    return (parts[0].strip(), parts[1].strip()) if len(parts)==2 else ("","")

def _load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = list(r)
        return r.fieldnames, rows

def _write_rows(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows: w.writerow(row)

def dedupe_csv(in_path, out_path, window_min=10, exact=False):
    fieldnames, rows = _load_rows(in_path)
    for col in ("timestamp_iso","artist","title","display_fallback"):
        if col not in fieldnames:
            fieldnames.append(col)
            for row in rows: row.setdefault(col, "")

    for row in rows:
        if not (row.get("artist") or "").strip() or not (row.get("title") or "").strip():
            a,t = _split_display(row.get("display_fallback",""))
            if a and not row.get("artist"): row["artist"]=a
            if t and not row.get("title"):  row["title"]=t

    original_count = len(rows)

    seen_exact, exact_rows = set(), []
    for row in rows:
        key = tuple((row.get(c,"") or "").strip() for c in ["timestamp_iso","artist","title","display_fallback"])
        if key in seen_exact: continue
        seen_exact.add(key)
        exact_rows.append(row)
    if exact:
        _write_rows(out_path, fieldnames, exact_rows)
        return {"original":original_count, "kept":len(exact_rows), "mode":"exact"}

    window = timedelta(minutes=max(0, int(window_min)))
    rows_sorted = sorted(exact_rows, key=lambda r: (_norm(r.get("artist","")),
                                                   _norm(r.get("title","")),
                                                   (_parse_iso(r.get("timestamp_iso","")) or datetime.max).timestamp()))
    kept, last_time = [], {}
    for row in rows_sorted:
        a, t = _norm(row.get("artist","")), _norm(row.get("title",""))
        ts = _parse_iso(row.get("timestamp_iso",""))
        key = (a, t)
        if ts is None:
            subkey = (a, t, _norm(row.get("display_fallback","")))
            s = last_time.get(key)
            if not isinstance(s, set):
                s=set(); last_time[key]=s
            if subkey in s: continue
            s.add(subkey); kept.append(row); continue
        last = last_time.get(key)
        if isinstance(last, datetime) and abs((ts-last)) <= window:
            continue
        kept.append(row); last_time[key]=ts

    kept_sorted = sorted(kept, key=lambda r: (_parse_iso(r.get("timestamp_iso","")) or datetime.min), reverse=True)
    _write_rows(out_path, fieldnames, kept_sorted)
    return {"original":original_count, "kept":len(kept_sorted), "mode":f"{window_min}min"}
