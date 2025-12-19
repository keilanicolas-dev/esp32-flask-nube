from flask import Flask, request, jsonify, render_template, Response
import psycopg2
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)

# =============================
# CONFIGURACIÓN DB (Render)
# =============================
DATABASE_URL = os.environ.get("DATABASE_URL")
MX_TZ = ZoneInfo("America/Mexico_City")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mediciones (
            id SERIAL PRIMARY KEY,
            ts TIMESTAMPTZ NOT NULL,
            voltaje REAL,
            corriente REAL,
            potencia REAL,
            radiometro REAL,
            temperatura REAL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

# =============================
# HELPERS
# =============================
def parse_ts_from_payload(data: dict) -> datetime:
    """
    Acepta:
      data["fecha"] = "YYYY-MM-DD HH:MM:SS" (hora local México)
    Devuelve:
      datetime con zona horaria en UTC (para guardarlo en Postgres como timestamptz)
    """
    s = data.get("fecha")
    if isinstance(s, str) and len(s) >= 19:
        # "2025-12-19 11:20:19"
        local_dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=MX_TZ)
        return local_dt.astimezone(timezone.utc)

    # fallback: hora del servidor en UTC
    return datetime.now(timezone.utc)

def to_float_or_none(x):
    if x is None:
        return None
    try:
        return float(x)
    except:
        return None

# =============================
# RUTAS
# =============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data", methods=["POST"])
def recibir_datos():
    data = request.get_json(silent=True) or {}

    ts_utc = parse_ts_from_payload(data)

    voltaje = to_float_or_none(data.get("voltaje"))
    corriente = to_float_or_none(data.get("corriente"))
    potencia = to_float_or_none(data.get("potencia"))
    radiometro = to_float_or_none(data.get("radiometro"))
    temperatura = to_float_or_none(data.get("temperatura"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mediciones (ts, voltaje, corriente, potencia, radiometro, temperatura)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (ts_utc, voltaje, corriente, potencia, radiometro, temperatura))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/data", methods=["GET"])
def obtener_datos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, ts, voltaje, corriente, potencia, radiometro, temperatura
        FROM mediciones
        ORDER BY id DESC
        LIMIT 300
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    datos = []
    for r in rows:
        _id = r[0]
        ts_utc = r[1]  # timestamptz
        # Convertimos a horario México para mostrar
        ts_mx = ts_utc.astimezone(MX_TZ)

        datos.append({
            "id": _id,
            "fecha": ts_mx.strftime("%Y-%m-%d"),
            "hora": ts_mx.strftime("%H:%M:%S"),
            "voltaje": r[2],
            "corriente": r[3],
            "potencia": r[4],
            "radiometro": r[5],
            "temperatura": r[6],
        })

    return jsonify(datos)

# (Opcional) CSV desde el server (si quisieras en vez de client-side)
@app.route("/api/csv", methods=["GET"])
def descargar_csv():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT ts, voltaje, corriente, potencia, radiometro, temperatura
        FROM mediciones
        ORDER BY id ASC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    lines = ["fecha,hora,voltaje,corriente,potencia,radiometro,temperatura"]
    for (ts_utc, v, c, p, r, t) in rows:
        ts_mx = ts_utc.astimezone(MX_TZ)
        lines.append("{},{},{},{},{},{},{}".format(
            ts_mx.strftime("%Y-%m-%d"),
            ts_mx.strftime("%H:%M:%S"),
            "" if v is None else v,
            "" if c is None else c,
            "" if p is None else p,
            "" if r is None else r,
            "" if t is None else t,
        ))

    csv_data = "\n".join(lines)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=mediciones.csv"}
    )
