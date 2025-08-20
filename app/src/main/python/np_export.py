# np_export.py
# Módulo que abre la DB de Now Playing y exporta a CSV.
# Usado por MainActivity.kt mediante Chaquopy.

import csv, datetime as dt, re, sqlite3
from pathlib import Path

LIKELY_TABLE_PATTERNS = [r"recognition", r"history", r"now_?playing", r"match", r"song", r"track"]
LIKELY_ARTIST_COLUMNS = ["artist","artist_name","singer","performer"]
LIKELY_TITLE_COLUMNS  = ["title","song","track","track_title","name"]
LIKELY_TIME_COLUMNS   = ["timestamp","time_millis","time_ms","created","created_millis",
                         "recognition_time","matched_time","played_time","date"]
LIKELY_DISPLAY_COLS   = ["display","display_text","text","label"]
EXTRA_COLS_CANDIDATES = ["album","album_name","source","confidence","score","deeplink",
                         "spotify_id","apple_id","deezer_id"]

def connect_sqlite(path):
    path = str(path)
    if not Path(path).is_file():
        raise FileNotFoundError(f"No existe la DB: {path}")
    uri = f"file:{path}?mode=ro"
    return sqlite3.connect(uri, uri=True)

def list_tables(conn):
    cur = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    return [(r[0], r[1] or "") for r in cur.fetchall()]

def get_columns(conn, table):
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]

def choose_column(cols, candidates):
    low = [c.lower() for c in cols]
    for c in candidates:
        if c in low:
            return cols[low.index(c)]
    return None

def find_best_mapping(cols):
    return {
        "artist": choose_column(cols, LIKELY_ARTIST_COLUMNS),
        "title":  choose_column(cols, LIKELY_TITLE_COLUMNS),
        "when":   choose_column(cols, LIKELY_TIME_COLUMNS),
        "display":choose_column(cols, LIKELY_DISPLAY_COLS),
        "extras": [x for x in (choose_column(cols,[c]) for c in EXTRA_COLS_CANDIDATES) if x]
    }

def pick_history_tables(tables):
    res = []
    for name, ddl in tables:
        n = name.lower()
        if any(re.search(p, n) for p in LIKELY_TABLE_PATTERNS):
            res.append((name, ddl)); continue
        ddl_low = (ddl or "").lower()
        if any(w in ddl_low for w in ["artist","title","song","track","timestamp"]):
            res.append((name, ddl))
    return res or tables

def to_iso(ts_value):
    try: t = int(ts_value)
    except Exception: return ""
    if t > 10_000_000_000:  # probablemente ms
        t = t / 1000.0
    return dt.datetime.utcfromtimestamp(t).isoformat() + "Z"

def export_from_table(conn, table, mapping, bucket):
    cols = get_columns(conn, table)
    sel = set(filter(None, [mapping["artist"], mapping["title"], mapping["when"], mapping["display"]]))
    for x in mapping["extras"]:
        sel.add(x)
    if not sel: return 0
    cur = conn.execute(f"SELECT {', '.join(sel)} FROM {table}")
    fetched = cur.fetchall()
    names = [d[0] for d in cur.description]
    n = 0
    for row in fetched:
        rec = dict(zip(names, row))
        artist = rec.get(mapping["artist"], "") if mapping["artist"] else ""
        title  = rec.get(mapping["title"], "")  if mapping["title"]  else ""
        when   = rec.get(mapping["when"], "")   if mapping["when"]   else ""
        disp   = rec.get(mapping["display"], "")if mapping["display"]else ""

        if (not artist or not title) and disp:
            parts = re.split(r"\s+[-—–]\s+", str(disp), maxsplit=1)
            if len(parts)==2:
                if not artist: artist = parts[0]
                if not title:  title  = parts[1]

        iso_time = to_iso(when) if str(when).strip() else ""
        extras = {f"extra_{k}":("" if v is None else str(v)) for k,v in rec.items()
                  if k in set(mapping["extras"])}

        if not (artist or title or disp):
            continue

        bucket.append({
            "timestamp_iso": iso_time,
            "artist": str(artist) if artist is not None else "",
            "title":  str(title)  if title  is not None else "",
            "display_fallback": str(disp) if disp is not None else "",
            **extras
        })
        n += 1
    return n

def export_csv(db_path, out_csv_path):
    conn = connect_sqlite(db_path)
    try:
        tables = list_tables(conn)
        hist = pick_history_tables(tables)
        rows = []
        total = 0
        for name,_ in hist:
            mapping = find_best_mapping(get_columns(conn, name))
            total += export_from_table(conn, name, mapping, rows)
        if total == 0:
            raise RuntimeError("No se encontraron filas exportables.")
        # union de cabeceras
        headers = sorted({k for r in rows for k in r.keys()})
        with open(out_csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for r in rows: w.writerow(r)
        return len(rows)
    finally:
        try: conn.close()
        except Exception: pass
