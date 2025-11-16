from flask import Flask, render_template, request, redirect, send_file, abort, jsonify
import sqlite3
import openpyxl
import io
from collections import defaultdict, Counter

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

# 🔮 Nueva ruta: predecir asignaciones óptimas (trading predictions)
@app.route("/predict", methods=["GET"])
def predict_trading():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, nombre, puesto, proyecto FROM trabajadores")
    trabajadores = c.fetchall()
    conn.close()
    
    # Analizar distribución actual
    project_counts = Counter()
    position_by_project = defaultdict(lambda: defaultdict(int))
    
    for t in trabajadores:
        worker_id, nombre, puesto, proyecto = t
        if proyecto:
            project_counts[proyecto] += 1
            position_by_project[proyecto][puesto] += 1
    
    # Calcular predicciones/sugerencias
    predictions = []
    
    # 1. Identificar desbalances de proyectos
    if len(project_counts) > 0:
        avg_workers = sum(project_counts.values()) / len(PROYECTOS)
        for proyecto in PROYECTOS:
            count = project_counts.get(proyecto, 0)
            balance = count - avg_workers
            predictions.append({
                'tipo': 'balance',
                'proyecto': proyecto,
                'trabajadores_actuales': count,
                'diferencia': round(balance, 1),
                'estado': 'sobrecargado' if balance > 1 else ('balanceado' if abs(balance) <= 1 else 'necesita_mas')
            })
    
    # 2. Sugerir redistribuciones específicas
    suggestions = []
    for t in trabajadores:
        worker_id, nombre, puesto, proyecto = t
        if not proyecto:
            # Sugerir proyecto para trabajadores sin asignación
            # Asignar al proyecto con menos trabajadores
            min_project = min(PROYECTOS, key=lambda p: project_counts.get(p, 0))
            suggestions.append({
                'trabajador': nombre,
                'puesto': puesto,
                'accion': 'asignar',
                'proyecto_sugerido': min_project,
                'razon': f'Proyecto con menor carga actual ({project_counts.get(min_project, 0)} trabajadores)'
            })
    
    # 3. Identificar necesidades por tipo de puesto
    position_needs = []
    for proyecto in PROYECTOS:
        positions = position_by_project[proyecto]
        total = project_counts.get(proyecto, 0)
        if total > 0:
            position_needs.append({
                'proyecto': proyecto,
                'puestos': dict(positions),
                'total': total
            })
    
    return jsonify({
        'balance_proyectos': predictions,
        'sugerencias_asignacion': suggestions,
        'necesidades_por_puesto': position_needs,
        'total_trabajadores': len(trabajadores),
        'proyectos': list(PROYECTOS)
    })




