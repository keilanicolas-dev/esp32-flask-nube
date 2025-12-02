from flask import Flask, request, jsonify, render_template
import json
import os

app = Flask(__name__)

DATA_FILE = "data.json"

# Crear archivo si no existe
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data", methods=["POST"])
def receive_data():
    new_entry = request.get_json()

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    data.append(new_entry)

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

    return jsonify({"status": "ok", "message": "Data saved"})

@app.route("/api/data", methods=["GET"])
def get_data():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
