# Panel Jefe de Turno Puerto - versión móvil

Aplicación Flask responsive y tipo PWA para registrar datos desde computador o celular usando `data.xlsx` como base.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Abrir en el celular dentro de la misma red Wi‑Fi

1. Ejecuta la app en tu computador.
2. Averigua la IP local del computador.
   - Windows: `ipconfig`
   - Mac/Linux: `ifconfig` o `ip addr`
3. En tu celular abre:

```text
http://TU_IP_LOCAL:5000
```

Ejemplo:

```text
http://192.168.1.25:5000
```

## Instalar como app en el teléfono

- iPhone (Safari): Compartir → "Agregar a pantalla de inicio"
- Android (Chrome): menú → "Instalar app" o "Agregar a pantalla de inicio"

## Notas

- La app escribe directamente sobre `data.xlsx`.
- Mantén una copia de respaldo del archivo.
- Para acceso fuera de tu red local, conviene publicarla en Render, Railway, Azure o un servidor interno.


## Publicación rápida

### Opción 1: enlace temporal para el celular
Instala Cloudflared o ngrok en el computador donde corre la app y luego ejecuta:

```bash
python app.py
```

En otra terminal con Cloudflared:

```bash
cloudflared tunnel --url http://127.0.0.1:5000
```

Te entregará un enlace HTTPS temporal para abrir desde el celular.

### Opción 2: Render
Sube esta carpeta a GitHub y despliega con `render.yaml`.
