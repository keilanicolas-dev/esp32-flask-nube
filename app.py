from flask import Flask, request, jsonify, render_template, Response
import os
import psycopg2
import urllib.parse as urlparse
from datetime import datetime
import csv
from io import StringIO

app = Flask(__name__)

# ========= CONFIGURACIÓN POSTGRES =========
DB_URL = os.environ.get("DATABASE_URL")

if not DB_URL:
    raise RuntimeError("DATABASE_URL no está definida en las variables de entorno")

# Parsear la URL de conexión
url = urlparse.urlparse(DB_URL)
DB_CONFIG = {
    "dbname": url.path[1:],
    "user": url.username,
    "password": url.password,
    "host": url.hostname,
    "port": url.port
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lecturas (
            id SERIAL PRIMARY KEY,
            fecha TEXT,
            voltaje1 DOUBLE PRECISION,
            voltaje2 DOUBLE PRECISION,
            corriente1 DOUBLE PRECISION,
            potencia1 DOUBLE PRECISION,
            radiometro DOUBLE PRECISION
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def insertar_lectura(fecha, v1, v2, c1, p1, rad):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO lecturas (fecha, voltaje1, voltaje2, corriente1, potencia1, radiometro)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (fecha, v1, v2, c1, p1, rad))
    conn.commit()
    cur.close()
    conn.close()

def obtener_ultimas(n=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT fecha, voltaje1, voltaje2, corriente1, potencia1, radiometro
        FROM lecturas
        ORDER BY id DESC
        LIMIT %s
    """, (n,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Orden cronológico ascendente
    rows.reverse()
    datos = []
    for r in rows:
        datos.append({
            "fecha": r[0],
            "voltaje1": r[1],
            "voltaje2": r[2],
            "corriente1": r[3],
            "potencia1": r[4],
            "radiometro": r[5]
        })
    return datos

def contar_todo():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM lecturas")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total

# ========= HOOK DE INICIO =========
@app.before_first_request
def before_first_request_func():
    init_db()

# ========= RUTAS =========

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data", methods=["POST"])
def api_recibir():
    """
    El ESP32 envía JSON con:
    {
      "fecha": "2025-12-02 15:30:00",
      "voltaje1": ...,
      "voltaje2": ...,
      "corriente1": ...,
      "potencia1": ...,
      "radiometro": ...
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibió JSON"}), 400

    try:
        fecha = data.get("fecha") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        v1 = float(data.get("voltaje1", 0))
        v2 = float(data.get("voltaje2", 0))
        c1 = float(data.get("corriente1", 0))
        p1 = float(data.get("potencia1", v1 * c1))
        rad = float(data.get("radiometro", 0))
    except Exception as e:
        return jsonify({"error": "Formato inválido", "detalle": str(e)}), 400

    insertar_lectura(fecha, v1, v2, c1, p1, rad)
    return jsonify({"status": "ok"}), 201

@app.route("/api/data", methods=["GET"])
def api_historial():
    """
    Devuelve las últimas N lecturas (por defecto 200)
    /api/data?n=200
    """
    n = request.args.get("n", default=200, type=int)
    datos = obtener_ultimas(n)
    return jsonify(datos)

@app.route("/api/count")
def api_count():
    total = contar_todo()
    return jsonify({"total": total})

@app.route("/api/csv")
def api_csv():
    """
    Devuelve las lecturas en CSV con fecha y hora separadas.
    """
    datos = obtener_ultimas(10000)

    output = StringIO()
    writer = csv.writer(output)

    # Encabezados
    writer.writerow([
        "Fecha",
        "Hora",
        "Voltaje 1 (V)",
        "Temperatura (°C)",
        "Corriente 1 (A)",
        "Potencia 1 (W)",
        "Radiometro (promedio LDR)"
    ])

    for d in datos:
        # Separar fecha/hora
        if d["fecha"]:
            partes = d["fecha"].split(" ")
            fecha_col = partes[0]
            hora_col = partes[1] if len(partes) > 1 else ""
        else:
            fecha_col = ""
            hora_col = ""

        writer.writerow([
            fecha_col,
            hora_col,
            d["voltaje1"],
            d["voltaje2"],
            d["corriente1"],
            d["potencia1"],
            d["radiometro"]
        ])

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=lecturas_esp32.csv"
        }
    )

# ========= SERVIDOR LOCAL (opcional) =========
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)

