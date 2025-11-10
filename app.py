from flask import Flask, request, jsonify
import csv
import os
from datetime import datetime

app = Flask(__name__)

CSV_FILE = "datos.csv"
CABECERA = ["fecha", "voltaje", "voltaje2", "corriente", "potencia1", "radiometro"]

# --- Ruta para recibir datos del ESP32 ---
@app.route("/enviar", methods=["POST"])
def recibir_datos():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    # Agregar fecha actual
    data["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Crear el archivo CSV si no existe
    existe = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CABECERA)
        if not existe:
            writer.writeheader()
        writer.writerow(data)

    return jsonify({"status": "ok", "data": data})

# --- Ruta para mostrar todos los datos guardados ---
@app.route("/datos", methods=["GET"])
def mostrar_datos():
    registros = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                registros.append(row)
    return jsonify(registros)

# --- Ruta principal para verificar conexión ---
@app.route("/")
def home():
    return "<h2>Servidor Flask funcionando correctamente 🚀</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
