# -*- coding: utf-8 -*-
# Basado en nowplaying_export.py de Brian: se elimina la copia con su y
# se expone una función export_csv(db_path, out_csv_path).
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

def debug_database_structure(db_path):
    """Función para debuggear la estructura real de la DB"""
    try:
        print("🔍 INICIANDO DEBUGGING...")
        conn = connect_sqlite(db_path)
        print("✅ Conexión a DB exitosa")
        
        tables = list_tables(conn)
        print(f"📊 Encontradas {len(tables)} tablas")
        
        for name, ddl in tables:
            print(f"\n📋 TABLA: {name}")
            print(f"DDL: {ddl[:200]}...")
            
            cols = get_columns(conn, name)
            print(f"Columnas: {cols}")
            
            # Mostrar algunas filas de ejemplo
            try:
                cur = conn.execute(f"SELECT * FROM {name} LIMIT 3")
                sample_rows = cur.fetchall()
                print(f"Muestra de datos:")
                for i, row in enumerate(sample_rows):
                    print(f"  Fila {i+1}: {row}")
            except Exception as e:
                print(f"Error al leer datos: {e}")
                
        conn.close()
        print("✅ Debugging completado")
        
    except Exception as e:
        print(f"❌ ERROR en debugging: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

def _coerce_bool_like(value):
    if value is None:
        return ""
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y", "t", "si", "sí"):  # soporta español
        return "1"
    if s in ("0", "false", "no", "n", "f"):
        return "0"
    return s  # deja tal cual si no es interpretable


def _normalize_rows_for_simple_csv(rows):
    """Convierte registros heterogéneos en filas simples con 4 columnas.
    - artist: tal cual si existe
    - title: usa title, o intenta partir display_fallback en "artista - título"
    - timestamp_iso: tal cual si existe
    - favorite: intenta deducir de cualquier extra que contenga 'fav'
    """
    normalized = []
    for r in rows:
        artist = (r.get("artist") or "").strip()
        title = (r.get("title") or "").strip()
        if not title:
            disp = (r.get("display_fallback") or "").strip()
            if disp:
                parts = re.split(r"\s+[-—–]\s+", disp, maxsplit=1)
                if len(parts) == 2:
                    # Si no hay artista, intenta tomar el de display
                    if not artist:
                        artist = parts[0].strip()
                    title = parts[1].strip() or title
                else:
                    # Si no tiene separador, como último recurso usa todo
                    if not title:
                        title = disp
        ts = (r.get("timestamp_iso") or "").strip()

        # Derivar favorito: busca cualquier clave que contenga 'fav'
        fav_val = ""
        for k, v in r.items():
            if "fav" in k.lower():
                fav_val = _coerce_bool_like(v)
                break

        normalized.append({
            "artist": artist,
            "title": title,
            "timestamp_iso": ts,
            "favorite": fav_val,
        })
    return normalized


def export_csv(db_path, out_csv_path):
    print("🚀 INICIANDO EXPORTACIÓN CSV...")
    print(f"📁 DB Path: {db_path}")
    print(f"📄 CSV Output: {out_csv_path}")
    
    try:
        print("🔍 INICIANDO DEBUGGING...")
        debug_database_structure(db_path)
        print("✅ Debugging completado exitosamente")
    except Exception as e:
        print(f"❌ ERROR en debugging: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    print("🔗 Conectando a la base de datos...")
    conn = connect_sqlite(db_path)
    print("✅ Conexión exitosa")
    
    try:
        print("📋 Listando tablas...")
        tables = list_tables(conn)
        print(f"📊 Encontradas {len(tables)} tablas: {[t[0] for t in tables]}")
        
        hist = pick_history_tables(tables)
        print(f"🎯 Tablas de historial seleccionadas: {[h[0] for h in hist]}")
        
        rows = []
        total = 0
        for name, _ in hist:
            print(f"🔄 Procesando tabla: {name}")
            mapping = find_best_mapping(get_columns(conn, name))
            print(f"🗺️ Mapeo encontrado: {mapping}")
            count = export_from_table(conn, name, mapping, rows)
            total += count
            print(f"📈 Exportadas {count} filas de {name}")
        
        print(f"📊 Total de filas exportadas: {total}")
        
        if total == 0:
            raise RuntimeError("No se encontraron filas exportables.")
        
        # Normalizar a 4 columnas fijas en orden deseado
        simple_rows = _normalize_rows_for_simple_csv(rows)
        headers = ["artist", "title", "timestamp_iso", "favorite"]
        print(f"📝 Headers del CSV (fijos): {headers}")
        
        with open(out_csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for r in simple_rows:
                w.writerow(r)
        
        print(f"💾 CSV guardado exitosamente en: {out_csv_path}")
        return len(simple_rows)
        
    finally:
        try: 
            conn.close()
            print("🔒 Conexión cerrada")
        except Exception as e:
            print(f"⚠️ Error al cerrar conexión: {e}")
