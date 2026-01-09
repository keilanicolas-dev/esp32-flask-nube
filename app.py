from flask import Flask, request, jsonify, render_template
import psycopg2
import os
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

MX_TZ = ZoneInfo("America/Mexico_City")

def init_db():
    conn = get_conn()
    cur = conn.cursor()

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

    # compatibilidad por si ya existía
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    now_mx = datetime.now(MX_TZ)
    return jsonify({"mx_time": now_mx.strftime("%Y-%m-%d %H:%M:%S"), "status": "ok"})

@app.route("/api/data", methods=["POST"])
def recibir_datos():
    data = request.get_json(force=True, silent=True) or {}

    device = (data.get("device") or "s2").strip().lower()

    now_mx = datetime.now(MX_TZ)
    fecha = now_mx.date()
    hora = now_mx.time().replace(microsecond=0)

    voltaje = data.get("voltaje")
    corriente = data.get("corriente")
    potencia = data.get("potencia")
    radiometro = data.get("radiometro")
    temperatura = data.get("temperatura")

    v1 = data.get("voltaje1"); v2 = data.get("voltaje2"); v3 = data.get("voltaje3")
    c1 = data.get("corriente1"); c2 = data.get("corriente2"); c3 = data.get("corriente3")
    p1 = data.get("potencia1"); p2 = data.get("potencia2"); p3 = data.get("potencia3")

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
        RETURNING id
    """, (
        device, now_mx, fecha, hora,
        voltaje, corriente, potencia, radiometro, temperatura,
        v1, v2, v3,
        c1, c2, c3,
        p1, p2, p3
    ))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok", "device": device, "id": new_id})

@app.route("/api/data", methods=["GET"])
def obtener_datos():
    device = (request.args.get("device") or "s2").strip().lower()

    # limit opcional
    try:
        limit = int(request.args.get("limit", "300"))
    except:
        limit = 300
    limit = max(1, min(limit, 5000))

    # since_id opcional (solo trae nuevos)
    since_id = request.args.get("since_id")
    since_id_val = None
    if since_id not in (None, "", "null", "undefined"):
        try:
            since_id_val = int(since_id)
        except:
            since_id_val = None

    conn = get_conn()
    cur = conn.cursor()

    if since_id_val is None:
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
    else:
        cur.execute("""
            SELECT id, device, fecha, hora,
                   voltaje, corriente, potencia, radiometro, temperatura,
                   voltaje1, voltaje2, voltaje3,
                   corriente1, corriente2, corriente3,
                   potencia1, potencia2, potencia3
            FROM mediciones
            WHERE device = %s AND id > %s
            ORDER BY id ASC
            LIMIT %s
        """, (device, since_id_val, limit))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    datos = []
    for r in rows:
        datos.append({
            "id": r[0],
            "device": r[1],
            "fecha": str(r[2]) if r[2] else None,
            "hora": str(r[3]) if r[3] else None,

            "voltaje": r[4],
            "corriente": r[5],
            "potencia": r[6],
            "radiometro": r[7],
            "temperatura": r[8],

            "voltaje1": r[9], "voltaje2": r[10], "voltaje3": r[11],
            "corriente1": r[12], "corriente2": r[13], "corriente3": r[14],
            "potencia1": r[15], "potencia2": r[16], "potencia3": r[17],
        })

    return jsonify(datos)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
