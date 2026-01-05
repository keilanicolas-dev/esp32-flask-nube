from flask import Flask, request, jsonify, render_template
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está configurada en Render (Environment Variables).")
    return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=10)

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    # Endpoint para probar rápido si DB conecta
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/data", methods=["POST"])
def recibir_datos():
    try:
        data = request.get_json(force=True) or {}

        # 1) Si el ESP manda fecha/hora (recomendado), se usan:
        fecha_str = data.get("fecha")  # "YYYY-MM-DD"
        hora_str  = data.get("hora")   # "HH:MM:SS" (sin microsegundos)

        if fecha_str and hora_str:
            # limpia microsegundos si llegan
            hora_str = hora_str.split(".")[0]
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            hora  = datetime.strptime(hora_str, "%H:%M:%S").time()
        else:
            # 2) Si no llega, usa el server time
            now = datetime.now()
            fecha = now.date()
            hora = now.time().replace(microsecond=0)

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
    except Exception as e:
        # Esto hace que SIEMPRE veas el motivo real del 500 en Render logs
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.route("/api/data", methods=["GET"])
def obtener_datos():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, fecha, hora, voltaje, corriente, potencia, radiometro, temperatura
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
                "id": r[0],
                "fecha": str(r[1]) if r[1] else None,
                "hora": str(r[2]) if r[2] else None,
                "voltaje": r[3],
                "corriente": r[4],
                "potencia": r[5],
                "radiometro": r[6],
                "temperatura": r[7]
            })

        return jsonify(datos)
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

