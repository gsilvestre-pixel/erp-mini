from flask import Flask, render_template, request, redirect, send_file, abort, url_for
import sqlite3
import openpyxl
import io
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# ▼▼▼ NUEVO: opciones fijas para el desplegable ▼▼▼
PROYECTOS = ("Rio La Leche", "Rio Motupe", "Rio Huaura")
# ▲▲▲

DB_NAME = "RRHH.db"

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

# 🎨 Nueva ruta: página de diseño artístico
@app.route("/diseno", methods=["GET"])
def diseno():
    # Obtener la última imagen subida
    uploaded_image = None
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
        if files:
            # Obtener el archivo más reciente
            files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
            uploaded_image = files[0]
    
    # Propuestas de siluetas
    siluetas = [
        {"nombre": "Deportiva Clásica", "descripcion": "Silueta aerodinámica con líneas fluidas"},
        {"nombre": "Urbana Minimalista", "descripcion": "Diseño limpio y elegante para uso diario"},
        {"nombre": "Alta Performance", "descripcion": "Silueta técnica optimizada para rendimiento"},
        {"nombre": "Casual Elegante", "descripcion": "Equilibrio entre comodidad y estilo"},
    ]
    
    # Propuestas de suelas
    suelas = [
        {"nombre": "Tracción Deportiva", "descripcion": "Patrón con hexágonos para máximo agarre"},
        {"nombre": "Comfort Plus", "descripcion": "Suela acolchada con amortiguación avanzada"},
        {"nombre": "Urbana Plana", "descripcion": "Diseño minimalista para superficies lisas"},
        {"nombre": "Todo Terreno", "descripcion": "Patrón agresivo para múltiples superficies"},
    ]
    
    return render_template("diseno.html", 
                         uploaded_image=uploaded_image,
                         siluetas=siluetas,
                         suelas=suelas)

# 🎨 Nueva ruta: subir imagen artística
@app.route("/subir_imagen", methods=["POST"])
def subir_imagen():
    if 'imagen' not in request.files:
        return redirect(url_for('diseno'))
    
    file = request.files['imagen']
    if file.filename == '':
        return redirect(url_for('diseno'))
    
    if file and allowed_file(file.filename):
        # Crear carpeta si no existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Guardar archivo con nombre seguro
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    return redirect(url_for('diseno'))



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
