from flask import Flask, request, jsonify, render_template
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# =====================================================
# CONFIGURACIÓN BASE DE DATOS (Render)
# =====================================================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id SERIAL PRIMARY KEY,
            fecha DATE,
            hora TIME,
            voltaje REAL,
            corriente REAL,
            potencia REAL,
            radiometro REAL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Inicializar BD (NO rompe el arranque si falla)
try:
    init_db()
except Exception as e:
    print("Error inicializando DB:", e)

# =====================================================
# RUTAS WEB
# =====================================================
@app.route("/")
def index():
    return render_template("index.html")

# =====================================================
# API: recibir datos del ESP32
# =====================================================
@app.route("/api/send", methods=["POST"])
def recibir_datos():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    ahora = datetime.now()
    fecha = ahora.date()
    hora = ahora.time()

    voltaje = data.get("voltaje")
    corriente = data.get("corriente")
    potencia = data.get("potencia")
    radiometro = data.get("radiometro")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO registros (fecha, hora, voltaje, corriente, potencia, radiometro)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (fecha, hora, voltaje, corriente, potencia, radiometro))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ok"}), 200

# =====================================================
# API: obtener datos para gráficas
# =====================================================
@app.route("/api/data")
def obtener_datos():
    limite = request.args.get("n", default=100, type=int)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT fecha, hora, voltaje, corriente, potencia, radiometro
            FROM registros
            ORDER BY id DESC
            LIMIT %s
        """, (limite,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    datos = []
    for r in reversed(rows):
        datos.append({
            "fecha": r[0].isoformat(),
            "hora": r[1].strftime("%H:%M:%S"),
            "voltaje": r[2],
            "corriente": r[3],
            "potencia": r[4],
            "radiometro": r[5]
        })

    return jsonify(datos)

