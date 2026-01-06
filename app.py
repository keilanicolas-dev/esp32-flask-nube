from flask import Flask, request, jsonify, render_template, Response
import psycopg2
import os
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

# =============================
# CONFIGURACIÓN DB (Render)
# =============================
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta DATABASE_URL en variables de entorno de Render")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

MX_TZ = ZoneInfo("America/Mexico_City")

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Tabla (si no existe)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mediciones (
            id SERIAL PRIMARY KEY,
            device TEXT NOT NULL DEFAULT 's2',
            ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            fecha DATE,
            hora TIME,

            -- ESP32 S2
            voltaje REAL,
            corriente REAL,
            potencia REAL,
            radiometro REAL,
            temperatura REAL,

            -- ESP32 WROOM (3 canales)
            voltaje1 REAL, voltaje2 REAL, voltaje3 REAL,
            corriente1 REAL, corriente2 REAL, corriente3 REAL,
            potencia1 REAL, potencia2 REAL, potencia3 REAL
        )
    """)

    # Si la tabla ya existía, asegura columnas (sin romper nada)
    cur.execute("ALTER TABLE mediciones ADD COLUMN IF NOT EXISTS device TEXT NOT NULL DEFAULT 's2';")
    cur.execute("ALTER TABLE mediciones ADD COLUMN IF NOT EXISTS ts TIMESTAMPTZ NOT NULL DEFAULT NOW();")
    cur.execute("ALTER TABLE mediciones ADD COLUMN IF NOT EXISTS fecha DATE;")
    cur.execute("ALTER TABLE mediciones ADD COLUMN IF NOT EXISTS hora TIME;")

    for col in ["voltaje","corriente","potencia","radiometro","temperatura"]:
        cur.execute(f"ALTER TABLE mediciones ADD COLUMN IF NOT EXISTS {col} REAL;")

    for col in [
        "voltaje1","voltaje2","voltaje3",
        "corriente1","corriente2","corriente3",
        "potencia1","potencia2","potencia3"
    ]:
        cur.execute(f"ALTER TABLE mediciones ADD COLUMN IF NOT EXISTS {col} REAL;")

    conn.commit()
    cur.close()
    conn.close()

init_db()

# =============================
# UTILIDADES
# =============================
def to_float_or_none(x):
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None

def now_mx():
    return datetime.now(MX_TZ)

def hora_str(t):
    # Siempre HH:MM:SS sin microsegundos
    if not t:
        return None
    return t.strftime("%H:%M:%S")

# =============================
# RUTAS
# =============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    n = now_mx()
    return jsonify({"mx_time": n.strftime("%Y-%m-%d %H:%M:%S"), "status": "ok"})

@app.route("/api/data", methods=["POST"])
def recibir_datos():
    data = request.get_json(force=True, silent=True) or {}

    device = (data.get("device") or "s2").strip().lower()

    n = now_mx()
    fecha = n.date()
    hora = n.time().replace(microsecond=0)  # ✅ guarda sin microsegundos

    # S2
    voltaje = to_float_or_none(data.get("voltaje"))
    corriente = to_float_or_none(data.get("corriente"))
    potencia = to_float_or_none(data.get("potencia"))
    radiometro = to_float_or_none(data.get("radiometro"))
    temperatura = to_float_or_none(data.get("temperatura"))

    # WROOM
    v1 = to_float_or_none(data.get("voltaje1"))
    v2 = to_float_or_none(data.get("voltaje2"))
    v3 = to_float_or_none(data.get("voltaje3"))
    c1 = to_float_or_none(data.get("corriente1"))
    c2 = to_float_or_none(data.get("corriente2"))
    c3 = to_float_or_none(data.get("corriente3"))
    p1 = to_float_or_none(data.get("potencia1"))
    p2 = to_float_or_none(data.get("potencia2"))
    p3 = to_float_or_none(data.get("potencia3"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mediciones
        (device, ts, fecha, hora,
         voltaje, corriente, potencia, radiometro, temperatura,
         voltaje1, voltaje2, voltaje3,
         corriente1, corriente2, corriente3,
         potencia1, potencia2, potencia3)
        VALUES
        (%s, %s, %s, %s,
         %s, %s, %s, %s, %s,
         %s, %s, %s,
         %s, %s, %s,
         %s, %s, %s)
    """, (
        device, n, fecha, hora,
        voltaje, corriente, potencia, radiometro, temperatura,
        v1, v2, v3,
        c1, c2, c3,
        p1, p2, p3
    ))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok", "device": device})

@app.route("/api/data", methods=["GET"])
def obtener_datos():
    device = (request.args.get("device") or "s2").strip().lower()
    limit = int(request.args.get("limit", "300"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, device, fecha, hora,
               voltaje, corriente, potencia, radiometro, temperatura,
               voltaje1, voltaje2, voltaje3,
               corriente1, corriente2, corriente3,
               potencia1, potencia2, potencia3
        FROM mediciones
        WHERE device = %s
        ORDER BY id DESC
        LIMIT %s
    """, (device, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    datos = []
    for r in rows:
        datos.append({
            "id": r[0],
            "device": r[1],
            "fecha": str(r[2]) if r[2] else None,
            "hora": hora_str(r[3]),  # ✅ HH:MM:SS sin microsegundos

            "voltaje": r[4],
            "corriente": r[5],
            "potencia": r[6],
            "radiometro": r[7],
            "temperatura": r[8],

            "voltaje1": r[9],  "voltaje2": r[10], "voltaje3": r[11],
            "corriente1": r[12],"corriente2": r[13],"corriente3": r[14],
            "potencia1": r[15], "potencia2": r[16], "potencia3": r[17],
        })

    return jsonify(datos)

# =============================
# CSV UNIFICADO (1 botón)
# =============================
@app.route("/api/csv", methods=["GET"])
def descargar_csv():
    limit = int(request.args.get("limit", "20000"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, hora,
               voltaje, corriente, potencia, radiometro, temperatura,
               voltaje1, voltaje2, voltaje3,
               corriente1, corriente2, corriente3,
               potencia1, potencia2, potencia3
        FROM mediciones
        ORDER BY id ASC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    header = [
        "id","fecha","hora",
        "voltaje","corriente","potencia","radiometro","temperatura",
        "voltaje1","voltaje2","voltaje3",
        "corriente1","corriente2","corriente3",
        "potencia1","potencia2","potencia3"
    ]

    def esc(v):
        if v is None:
            return ""
        return str(v)

    def generate():
        yield ",".join(header) + "\n"
        for r in rows:
            h = r[2].strftime("%H:%M:%S") if r[2] else ""
            fila = [
                r[0], r[1], h,
                r[3], r[4], r[5], r[6], r[7],
                r[8], r[9], r[10],
                r[11], r[12], r[13],
                r[14], r[15], r[16]
            ]
            yield ",".join(esc(x) for x in fila) + "\n"

    n = now_mx()
    filename = f"mediciones_{n.strftime('%Y-%m-%d_%H%M')}.csv"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# Render usa gunicorn; esto solo es para local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
