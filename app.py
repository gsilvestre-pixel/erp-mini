from flask import Flask, render_template, request, redirect, send_file, abort
import sqlite3
import openpyxl
import io

app = Flask(__name__)
# ▼▼▼ NUEVO: opciones fijas para el desplegable ▼▼▼
PROYECTOS = ("Rio La Leche", "Rio Motupe", "Rio Huaura")
# ▲▲▲

DB_NAME = "RRHH.db"

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

def ensure_column():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("PRAGMA table_info(trabajadores)")
    columnas = [col[1] for col in c.fetchall()]
    if "proyecto" not in columnas:
        c.execute("ALTER TABLE trabajadores ADD COLUMN proyecto TEXT")
        conn.commit()
    conn.close()

init_db()
ensure_column()

@app.route("/", methods=["GET"])
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM trabajadores")
    trabajadores = c.fetchall()
    conn.close()
    return render_template("index.html", trabajadores=trabajadores, PROYECTOS=PROYECTOS)

@app.route("/agregar", methods=["POST"])
def agregar():
    nombre = request.form["nombre"]
    puesto = request.form["puesto"]
    proyecto = (request.form["proyecto"] or "").strip()
    # Valida que "proyecto" sea uno de los 3 permitidos:
    if proyecto not in PROYECTOS:
    abort(400, description="Proyecto inválido")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO trabajadores (nombre, puesto, proyecto) VALUES (?, ?, ?)", (nombre, puesto, proyecto))
    conn.commit()
    conn.close()

    return redirect("/")

# 📤 Nueva ruta: exportar a Excel
@app.route("/exportar", methods=["GET"])
def exportar():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM trabajadores")
    trabajadores = c.fetchall()
    conn.close()

    # Crear libro Excel en memoria
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Trabajadores"

    # Encabezados
    ws.append(["ID", "Nombre", "Puesto","Proyecto"])

    # Datos
    for t in trabajadores:
        ws.append(t)

    # Guardar en memoria y enviar
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output, as_attachment=True,
                     download_name="trabajadores.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")



