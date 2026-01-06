from flask import Flask, request, jsonify, render_template
import os
import psycopg2
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

# =============================
# CONFIG DB
# =============================
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está configurada en Render (Environment Variables)")

TZ_MX = ZoneInfo("America/Mexico_City")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mediciones (
            id SERIAL PRIMARY KEY,
            fecha DATE NOT NULL,
            hora  TIME NOT NULL,
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
# RUTAS
# =============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    now_mx = datetime.now(TZ_MX)
    return jsonify({
        "mx_time": now_mx.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "ok"
    })

@app.route("/api/data", methods=["POST"])
def recibir_datos():
    data = request.get_json(silent=True) or {}

    now_mx = datetime.now(TZ_MX)
    fecha = now_mx.date()
    hora  = now_mx.time().replace(microsecond=0)

    # Lee valores que manda el ESP (sin fecha/hora del ESP)
    voltaje     = data.get("voltaje")
    corriente   = data.get("corriente")
    potencia    = data.get("potencia")
    radiometro  = data.get("radiometro")
    temperatura = data.get("temperatura")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mediciones (fecha, hora, voltaje, corriente, potencia, radiometro, temperatura)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (fecha, hora, voltaje, corriente, potencia, radiometro, temperatura))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/data", methods=["GET"])
def obtener_datos():
    limit = 300
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, hora, voltaje, corriente, potencia, radiometro, temperatura
        FROM mediciones
        ORDER BY id DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    datos = []
    for r in rows:
        datos.append({
            "id": r[0],
            "fecha": str(r[1]),
            "hora": str(r[2]),  # ya viene como HH:MM:SS
            "voltaje": r[3],
            "corriente": r[4],
            "potencia": r[5],
            "radiometro": r[6],
            "temperatura": r[7],
        })

    return jsonify(datos)

# LOCAL
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
