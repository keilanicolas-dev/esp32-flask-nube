from flask import Flask, request, jsonify, render_template, Response
import sqlite3
import os
from datetime import datetime
import csv
from io import StringIO

app = Flask(__name__)

DB_FILE = "datos.db"

# ========= DB helpers =========
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS lecturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            voltaje1 REAL,
            voltaje2 REAL,
            corriente1 REAL,
            potencia1 REAL,
            radiometro REAL
        )
    """)
    conn.commit()
    conn.close()

def insertar_lectura(fecha, v1, v2, c1, p1, rad):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO lecturas (fecha, voltaje1, voltaje2, corriente1, potencia1, radiometro)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (fecha, v1, v2, c1, p1, rad))
    conn.commit()
    conn.close()

def obtener_ultimas(n=100):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT fecha, voltaje1, voltaje2, corriente1, potencia1, radiometro
        FROM lecturas
        ORDER BY id DESC
        LIMIT ?
    """, (n,))
    rows = c.fetchall()
    conn.close()
    rows.reverse()  # para que queden en orden cronológico
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

# ========= Rutas =========

@app.route("/")
def home():
    # Dashboard con gráficas
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

@app.route("/api/csv")
def api_csv():
    """
    Devuelve las lecturas en CSV para descarga.
    """
    datos = obtener_ultimas(10000)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["fecha", "voltaje1", "voltaje2", "corriente1", "potencia1", "radiometro"])
    for d in datos:
        writer.writerow([
            d["fecha"],
            d["voltaje1"],
            d["voltaje2"],
            d["corriente1"],
            d["potencia1"],
            d["radiometro"],
        ])

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=lecturas_esp32.csv"
        }
    )

# ========= Arranque local =========
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)


