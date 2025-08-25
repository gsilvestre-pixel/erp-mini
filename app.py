# archivo: app.py
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB = "rrhh.db"

# Crear tabla si no existe
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trabajadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    dni TEXT,
                    area TEXT,
                    cargo TEXT,
                    estado TEXT
                )''')
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "HEAD"])
def index():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM trabajadores")
    trabajadores = c.fetchall()
    conn.close()
    return render_template("index.html", trabajadores=trabajadores)

@app.route("/agregar", methods=["POST"])
def agregar():
    nombre = request.form["nombre"]
    dni = request.form["dni"]
    area = request.form["area"]
    cargo = request.form["cargo"]
    estado = request.form["estado"]
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO trabajadores (nombre, dni, area, cargo, estado) VALUES (?,?,?,?,?)",
              (nombre, dni, area, cargo, estado))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/eliminar/<int:id>")
def eliminar(id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM trabajadores WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

