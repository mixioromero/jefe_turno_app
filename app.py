from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, range_boundaries
from datetime import datetime
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / 'data.xlsx'
STATIC_DIR = BASE_DIR / 'static'

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET_KEY', 'jefe-turno-puerto')

SHEETS_CONFIG = {
    'Bloqueos Activos': {'table': 'Bloqueos_Activos', 'title': 'Bloqueos Activos', 'icon': '🔒'},
    'ART': {'table': 'ART', 'title': 'ART', 'icon': '🦺'},
    'Checklist Moviles': {'table': 'Checklist_Moviles', 'title': 'Checklist Móviles', 'icon': '🚜'},
    'Checklist Fijos': {'table': 'Checklist_Fijos', 'title': 'Checklist Fijos', 'icon': '🏗️'},
    'PTS': {'table': 'PTS', 'title': 'PTS', 'icon': '📘'},
    'Anomalías': {'table': 'Anomalías', 'title': 'Anomalías', 'icon': '⚠️'},
    'Avisos SAP': {'table': 'Avisos_SAP', 'title': 'Avisos SAP', 'icon': '🛠️'},
    'Bitácora Turno': {'table': 'Bitácora_Turno', 'title': 'Bitácora Turno', 'icon': '📝'},
    'Entrega Turno': {'table': 'Entrega_Turno', 'title': 'Entrega de Turno', 'icon': '🤝'},
    'Asignacion VHF': {'table': 'Asignacion_VHF', 'title': 'Asignación VHF', 'icon': '📻'},
}

MASTER_TO_OPTIONS = {
    'Estado': 'Estados',
    'Estado final': 'Estados',
    'Prioridad': 'Prioridades',
    'Tipo': 'Tipos_Anomalia',
    'Turno': 'Turnos',
    'Turno saliente': 'Turnos',
    'Turno entrante': 'Turnos',
    'Combustible': 'Estados_OK',
    'Aceite motor': 'Estados_OK',
    'Aceite hidráulico': 'Estados_OK',
    'Refrigerante': 'Estados_OK',
    'Luces': 'Estados_OK',
    'Alarma': 'Estados_OK',
    'Neumáticos': 'Estados_OK',
    'Fugas': 'Estados_OK',
    'Cabina': 'Estados_OK',
    'Frenos': 'Estados_OK',
    'Extintor': 'Estados_OK',
    'Estructura': 'Estados_OK',
    'Motor': 'Estados_OK',
    'Guardas': 'Estados_OK',
    'Sensores': 'Estados_OK',
    'Polines': 'Estados_OK',
    'Correas': 'Estados_OK',
    'Chutes': 'Estados_OK',
    'Tolvas': 'Estados_OK',
    'Alimentadores': 'Estados_OK',
    'Captadores': 'Estados_OK',
    'Nebulizador': 'Estados_OK',
    'Impacto': 'Impactos',
}

DATE_FIELDS = {'Fecha', 'Cierre', 'Próx revisión'}
TIME_FIELDS = {'Hora', 'Hora liberación', 'Hora Entrega', 'Hora Devolución'}
NUMERIC_FIELDS = {'Personal', 'Canal', 'Horómetro', 'Equipos OK', 'Equipos falla', 'Bloqueos', 'Avisos SAP'}
TEXTAREA_FIELDS = {'Motivo', 'Obs', 'Observación', 'Descripción', 'Acción', 'Comentarios', 'Pendientes', 'Recomendaciones', 'Observaciones', 'Riesgos', 'Consecuencias', 'Medidas'}
AUTONUMERIC_FIELDS = {'ID'}


def load_wb():
    return load_workbook(EXCEL_PATH)


def get_headers(ws):
    return [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]


def get_master_lists(wb):
    ws = wb['MAESTRO_LISTAS']
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    lists = {}
    for idx, header in enumerate(headers, start=1):
        values = []
        for r in range(2, ws.max_row + 1):
            value = ws.cell(r, idx).value
            if value not in (None, ''):
                values.append(str(value))
        lists[header] = values
    return lists


def recent_rows(ws, limit=10):
    headers = get_headers(ws)
    rows = []
    for r in range(ws.max_row, 1, -1):
        vals = [ws.cell(r, c).value for c in range(1, len(headers) + 1)]
        if any(v not in (None, '') for v in vals):
            rows.append(dict(zip(headers, vals)))
        if len(rows) >= limit:
            break
    return rows


def dashboard_counts(wb):
    counts = {}
    checks = [
        ('Bloqueos Activos', 'Estado', lambda v: str(v).strip().lower() == 'activo'),
        ('Anomalías', 'Estado', lambda v: str(v).strip().lower() != 'cerrada'),
        ('Avisos SAP', 'Estado', lambda v: str(v).strip().lower() == 'abierto'),
        ('Bitácora Turno', 'Hora', lambda v: v not in (None, '')),
    ]
    for sheet_name, field, predicate in checks:
        ws = wb[sheet_name]
        headers = get_headers(ws)
        idx = headers.index(field) + 1
        total = 0
        for r in range(2, ws.max_row + 1):
            value = ws.cell(r, idx).value
            if predicate(value):
                total += 1
        counts[sheet_name] = total
    return counts


def infer_input_type(header):
    if header in AUTONUMERIC_FIELDS:
        return 'autonumber'
    if header in DATE_FIELDS:
        return 'date'
    if header in TIME_FIELDS:
        return 'time'
    if header in NUMERIC_FIELDS:
        return 'number'
    if header in TEXTAREA_FIELDS:
        return 'textarea'
    return 'text'


def next_id_value(ws, header):
    headers = get_headers(ws)
    idx = headers.index(header) + 1
    max_id = 0
    for r in range(2, ws.max_row + 1):
        value = ws.cell(r, idx).value
        try:
            max_id = max(max_id, int(value))
        except Exception:
            continue
    return max_id + 1


def parse_value(header, value, ws=None):
    if header in AUTONUMERIC_FIELDS and ws is not None:
        return next_id_value(ws, header)
    if value is None:
        return None
    value = value.strip() if isinstance(value, str) else value
    if value == '':
        return None
    if header in DATE_FIELDS:
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except Exception:
            return value
    if header in TIME_FIELDS:
        try:
            return datetime.strptime(value, '%H:%M').time()
        except Exception:
            return value
    if header in NUMERIC_FIELDS:
        try:
            return int(value)
        except Exception:
            try:
                return float(value)
            except Exception:
                return value
    return value


def append_row_and_expand_table(ws, table_name, row_data):
    next_row = ws.max_row + 1
    for col_idx, value in enumerate(row_data, start=1):
        ws.cell(next_row, col_idx, value)

    table = ws.tables[table_name]
    min_col, min_row, max_col, max_row = range_boundaries(table.ref)
    if next_row > max_row:
        table.ref = f"{get_column_letter(min_col)}{min_row}:{get_column_letter(max_col)}{next_row}"


def today_iso():
    return datetime.now().strftime('%Y-%m-%d')


def now_hhmm():
    return datetime.now().strftime('%H:%M')


def get_default_value(header, ws=None):
    if header in AUTONUMERIC_FIELDS and ws is not None:
        return str(next_id_value(ws, header))
    if header in DATE_FIELDS:
        return today_iso()
    if header in TIME_FIELDS:
        return now_hhmm()
    return ''


@app.route('/')
def index():
    wb = load_wb()
    counts = dashboard_counts(wb)
    modules = []
    for sheet_name, cfg in SHEETS_CONFIG.items():
        modules.append({
            'sheet_name': sheet_name,
            'title': cfg['title'],
            'icon': cfg['icon'],
            'count': counts.get(sheet_name, ''),
        })
    return render_template('index.html', modules=modules)


@app.route('/form/<path:sheet_name>', methods=['GET', 'POST'])
def form_sheet(sheet_name):
    wb = load_wb()
    if sheet_name not in SHEETS_CONFIG:
        flash('Módulo no encontrado.', 'error')
        return redirect(url_for('index'))

    ws = wb[sheet_name]
    headers = get_headers(ws)
    masters = get_master_lists(wb)

    if request.method == 'POST':
        row_data = []
        for header in headers:
            raw = request.form.get(header, '')
            row_data.append(parse_value(header, raw, ws))
        append_row_and_expand_table(ws, SHEETS_CONFIG[sheet_name]['table'], row_data)
        wb.save(EXCEL_PATH)
        flash(f'Registro guardado en {SHEETS_CONFIG[sheet_name]["title"]}.', 'success')
        return redirect(url_for('form_sheet', sheet_name=sheet_name))

    fields = []
    for header in headers:
        input_type = infer_input_type(header)
        fields.append({
            'name': header,
            'label': header,
            'type': input_type,
            'options': masters.get(MASTER_TO_OPTIONS.get(header, ''), []),
            'default': get_default_value(header, ws),
            'readonly': input_type == 'autonumber',
        })

    return render_template(
        'form.html',
        sheet_name=sheet_name,
        title=SHEETS_CONFIG[sheet_name]['title'],
        icon=SHEETS_CONFIG[sheet_name]['icon'],
        fields=fields,
        rows=recent_rows(ws),
    )


@app.route('/manifest.webmanifest')
def manifest():
    return send_from_directory(STATIC_DIR, 'manifest.webmanifest', mimetype='application/manifest+json')


@app.route('/service-worker.js')
def service_worker():
    return send_from_directory(STATIC_DIR, 'service-worker.js', mimetype='application/javascript')


@app.route('/health')
def health():
    return {'status': 'ok'}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=True, host='0.0.0.0', port=port)
