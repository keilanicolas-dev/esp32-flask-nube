from flask import Flask, request, jsonify, render_template, Response
import os
import psycopg2
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# =========================================
# CONFIGURACIÓN DB (Render)
# =========================================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está configurada en Render (Environment Variables).")
    # Render Postgres normalmente requiere ssl
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

# Inicializa DB al arrancar
try:
    init_db()
except Exception as e:
    # Importante: en Render, esto ayuda a ver el error en Logs
    print("ERROR init_db():", repr(e))


# =========================================
# UTIL: hora local (México UTC-6)
# =========================================
MX_TZ = timezone(timedelta(hours=-6))

def now_mx():
    # Render suele correr en UTC, convertimos a MX sin tocar ESP32
    return datetime.now(timezone.utc).astimezone(MX_TZ)

def safe_float(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


# =========================================
# RUTAS
# =========================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    # Prueba simple de DB + hora
    try:
        t = now_mx()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "mx_time": t.strftime("%Y-%m-%d %H:%M:%S")})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.route("/api/data", methods=["POST"])
def recibir_datos():
    try:
        data = request.get_json(silent=True) or {}

        t = now_mx()
        fecha = t.date()
        hora  = t.time().replace(microsecond=0)

        voltaje = safe_float(data.get("voltaje"))
        corriente = safe_float(data.get("corriente"))
        potencia = safe_float(data.get("potencia"))
        radiometro = safe_float(data.get("radiometro"))
        temperatura = safe_float(data.get("temperatura"))

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO mediciones
            (fecha, hora, voltaje, corriente, potencia, radiometro, temperatura)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (fecha, hora, voltaje, corriente, potencia, radiometro, temperatura))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "ok"})

    except Exception as e:
        # Esto te ayuda a ver el error real en Logs de Render
        print("ERROR /api/data POST:", repr(e))
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.route("/api/data", methods=["GET"])
def obtener_datos():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, fecha, hora, voltaje, corriente, potencia, radiometro, temperatura
            FROM mediciones
            ORDER BY fecha DESC, hora DESC, id DESC
            LIMIT 300
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        datos = []
        for r in rows:
            datos.append({
                "id": r[0],
                "fecha": str(r[1]),
                "hora": str(r[2]),
                "voltaje": r[3],
                "corriente": r[4],
                "potencia": r[5],
                "radiometro": r[6],
                "temperatura": r[7]
            })

        return jsonify(datos)

    except Exception as e:
        print("ERROR /api/data GET:", repr(e))
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.route("/api/csv", methods=["GET"])
def descargar_csv():
    """
    Descarga CSV con columnas separadas:
    fecha,hora,voltaje,corriente,potencia,radiometro,temperatura
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT fecha, hora, voltaje, corriente, potencia, radiometro, temperatura
            FROM mediciones
            ORDER BY fecha ASC, hora ASC, id ASC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        def gen():
            yield "fecha,hora,voltaje,corriente,potencia,radiometro,temperatura\n"
            for (f, h, v, c, p, r, t) in rows:
                # quita microsegundos si llegaran a aparecer
                h_str = str(h).split(".")[0] if h else ""
                yield f"{f},{h_str},{v if v is not None else ''},{c if c is not None else ''},{p if p is not None else ''},{r if r is not None else ''},{t if t is not None else ''}\n"

        filename = f"esp32_{now_mx().strftime('%Y-%m-%d_%H%M%S')}.csv"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        return Response(gen(), mimetype="text/csv", headers=headers)

    except Exception as e:
        print("ERROR /api/csv:", repr(e))
        return jsonify({"status": "error", "detail": str(e)}), 500


# =========================================
# LOCAL ONLY
# =========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
