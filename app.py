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
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("PRAGMA table_info(trabajadores)")
        columnas = [col[1] for col in c.fetchall()]
        if "proyecto" in columnas:
            return

        try:
            c.execute("ALTER TABLE trabajadores ADD COLUMN proyecto TEXT DEFAULT ''")
        except sqlite3.OperationalError as e:
            # Si otro worker ya la creó, ignora; si es otro error, relanza
            if "duplicate column name" not in str(e).lower():
                raise
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
    nombre = (request.form.get("nombre") or "").strip()
    puesto  = (request.form.get("puesto")  or "").strip()
    proyecto = (request.form.get("proyecto") or "").strip()
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
    c.execute("SELECT * FROM trabajadores ORDER BY nombre")
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




