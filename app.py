from flask import Flask, render_template, request, redirect, send_file, abort, url_for
import sqlite3
import openpyxl
import io
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
# ▼▼▼ NUEVO: opciones fijas para el desplegable ▼▼▼
PROYECTOS = ("Rio La Leche", "Rio Motupe", "Rio Huaura")
# ▲▲▲

DB_NAME = "RRHH.db"
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        # Add proyecto column if it doesn't exist
        if "proyecto" not in columnas:
            try:
                c.execute("ALTER TABLE trabajadores ADD COLUMN proyecto TEXT DEFAULT ''")
            except sqlite3.OperationalError as e:
                # Si otro worker ya la creó, ignora; si es otro error, relanza
                if "duplicate column name" not in str(e).lower():
                    raise
        
        # Add imagen column if it doesn't exist
        if "imagen" not in columnas:
            try:
                c.execute("ALTER TABLE trabajadores ADD COLUMN imagen TEXT DEFAULT ''")
            except sqlite3.OperationalError as e:
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
    
    # Handle file upload
    imagen_filename = ""
    if 'imagen' in request.files:
        file = request.files['imagen']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            timestamp = str(int(time.time() * 1000))
            filename = f"{timestamp}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagen_filename = filename
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO trabajadores (nombre, puesto, proyecto, imagen) VALUES (?, ?, ?, ?)", 
              (nombre, puesto, proyecto, imagen_filename))
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
    ws.append(["ID", "Nombre", "Puesto", "Proyecto", "Imagen"])

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




