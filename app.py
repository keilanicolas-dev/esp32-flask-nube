from flask import Flask, request, jsonify, render_template
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta DATABASE_URL en Render -> Environment Variables")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Tabla (si ya existe, no la rompe)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mediciones (
            id SERIAL PRIMARY KEY,
            device TEXT DEFAULT 's2',
            fecha DATE NOT NULL,
            hora TIME NOT NULL,

            -- S2 / base (compatibilidad)
            voltaje REAL,
            corriente REAL,
            potencia REAL,
            radiometro REAL,
            temperatura REAL,

            -- Canales extra (para WROOM u otros)
            voltaje1 REAL, voltaje2 REAL, voltaje3 REAL,
            corriente1 REAL, corriente2 REAL, corriente3 REAL,
            potencia1 REAL, potencia2 REAL, potencia3 REAL
        )
    """)

    # Si tu tabla ya existía sin estas columnas, las agrega sin perder datos
    cur.execute("ALTER TABLE mediciones ADD COLUMN IF NOT EXISTS device TEXT DEFAULT 's2';")

    for col in [
        "voltaje1 REAL", "voltaje2 REAL", "voltaje3 REAL",
        "corriente1 REAL", "corriente2 REAL", "corriente3 REAL",
        "potencia1 REAL", "potencia2 REAL", "potencia3 REAL",
        "voltaje REAL", "corriente REAL", "potencia REAL",
        "radiometro REAL", "temperatura REAL"
    ]:
        cur.execute(f"ALTER TABLE mediciones ADD COLUMN IF NOT EXISTS {col};")

    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    # Si ya corregiste hora México en app.py antes, déjalo como lo tienes.
    # Aquí solo confirmamos que está vivo.
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({"time": now, "status": "ok"})

@app.route("/api/data", methods=["POST"])
def recibir_datos():
    data = request.get_json(silent=True) or {}

    # Hora del servidor (si ya la tienes en MX con ZoneInfo, usa esa versión)
    now = datetime.now()
    fecha = now.date()
    hora = now.time().replace(microsecond=0)

    device = (data.get("device") or "s2").strip().lower()

    # Compatibilidad:
    # - S2 manda: voltaje, corriente, potencia, radiometro, temperatura
    # - WROOM mandará: voltaje1..3, corriente1..3, potencia1..3 (y opcional voltaje/corriente/potencia base)
    voltaje = data.get("voltaje")
    corriente = data.get("corriente")
    potencia = data.get("potencia")
    radiometro = data.get("radiometro")
    temperatura = data.get("temperatura")

    # Canales (si no vienen, quedan NULL)
    v1 = data.get("voltaje1")
    v2 = data.get("voltaje2")
    v3 = data.get("voltaje3")

    c1 = data.get("corriente1")
    c2 = data.get("corriente2")
    c3 = data.get("corriente3")

    p1 = data.get("potencia1")
    p2 = data.get("potencia2")
    p3 = data.get("potencia3")

    # Si no mandan base pero sí canal 1, rellenamos base con canal 1 (útil para gráficos viejos)
    if voltaje is None and v1 is not None:
        voltaje = v1
    if corriente is None and c1 is not None:
        corriente = c1
    if potencia is None and p1 is not None:
        potencia = p1

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mediciones (
          device, fecha, hora,
          voltaje, corriente, potencia, radiometro, temperatura,
          voltaje1, voltaje2, voltaje3,
          corriente1, corriente2, corriente3,
          potencia1, potencia2, potencia3
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        device, fecha, hora,
        voltaje, corriente, potencia, radiometro, temperatura,
        v1, v2, v3, c1, c2, c3, p1, p2, p3
    ))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok", "device": device})

@app.route("/api/data", methods=["GET"])
def obtener_datos():
    device = (request.args.get("device") or "").strip().lower()
    limit = request.args.get("limit") or "300"

    try:
        limit = int(limit)
        if limit < 1:
            limit = 300
        if limit > 2000:
            limit = 2000
    except:
        limit = 300

    conn = get_conn()
    cur = conn.cursor()

    if device:
        cur.execute("""
            SELECT
              id, device, fecha, hora,
              voltaje, corriente, potencia, radiometro, temperatura,
              voltaje1, voltaje2, voltaje3,
              corriente1, corriente2, corriente3,
              potencia1, potencia2, potencia3
            FROM mediciones
            WHERE device=%s
            ORDER BY id DESC
            LIMIT %s
        """, (device, limit))
    else:
        cur.execute("""
            SELECT
              id, device, fecha, hora,
              voltaje, corriente, potencia, radiometro, temperatura,
              voltaje1, voltaje2, voltaje3,
              corriente1, corriente2, corriente3,
              potencia1, potencia2, potencia3
            FROM mediciones
            ORDER BY id DESC
            LIMIT %s
        """, (limit,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "id": r[0],
            "device": r[1],
            "fecha": str(r[2]),
            "hora": str(r[3]),

            "voltaje": r[4],
            "corriente": r[5],
            "potencia": r[6],
            "radiometro": r[7],
            "temperatura": r[8],

            "voltaje1": r[9],  "voltaje2": r[10], "voltaje3": r[11],
            "corriente1": r[12],"corriente2": r[13],"corriente3": r[14],
            "potencia1": r[15], "potencia2": r[16], "potencia3": r[17],
        })

    return jsonify(out)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
