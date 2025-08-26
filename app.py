from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

DB_NAME = "RRHH.db"   # 👈 Usa tu archivo real

# Crear tabla si no existe
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trabajadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            puesto TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Página principal: lista de trabajadores
@app.route("/", methods=["GET"])
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM trabajadores")
    trabajadores = c.fetchall()
    conn.close()
    return render_template("index.html", trabajadores=trabajadores)

# Agregar nuevo trabajador
@app.route("/agregar", methods=["POST"])
def agregar():
    nombre = request.form["nombre"]
    puesto = request.form["puesto"]

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO trabajadores (nombre, puesto) VALUES (?, ?)", (nombre, puesto))
    conn.commit()
    conn.close()

    return redirect("/")

# Ejecutar app localmente
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
