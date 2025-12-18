from flask import Flask, request, jsonify, render_template
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# =============================
# CONFIGURACIÓN DB (Render)
# =============================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mediciones (
            id SERIAL PRIMARY KEY,
            fecha DATE,
            hora TIME,
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

# Inicializa DB al arrancar
init_db()

# =============================
# RUTAS
# =============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data", methods=["POST"])
def recibir_datos():
    data = request.json

    fecha = datetime.now().date()
    hora = datetime.now().time()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mediciones
        (fecha, hora, voltaje, corriente, potencia, radiometro, temperatura)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        fecha,
        hora,
        data.get("voltaje"),
        data.get("corriente"),
        data.get("potencia"),
        data.get("radiometro"),
        data.get("temperatura")
    ))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/data", methods=["GET"])
def obtener_datos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT fecha, hora, voltaje, corriente, potencia, radiometro, temperatura
        FROM mediciones
        ORDER BY id DESC
        LIMIT 300
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    datos = []
    for r in rows:
        datos.append({
            "fecha": str(r[0]),
            "hora": str(r[1]),
            "voltaje": r[2],
            "corriente": r[3],
            "potencia": r[4],
            "radiometro": r[5],
            "temperatura": r[6]
        })

    return jsonify(datos)

# =============================
# SOLO PARA LOCAL (NO Render)
# =============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



