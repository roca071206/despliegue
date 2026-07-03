"""
VISTAS PARA RESPALDO Y RESTAURACION DE BD
Permite crear respaldo completo y restaurarlo desde archivo SQL.
"""
import os
import subprocess
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from app.decorators import superadmin_required
import platform
import shutil


def obtener_credenciales_mysql():
    db_config = settings.DATABASES['default']
    return {
        'host':       db_config.get('HOST', 'localhost'),
        'user':       db_config.get('USER', 'root'),
        'password':   db_config.get('PASSWORD', ''),
        'database':   db_config.get('NAME', 'proyecto'),
        'port':       db_config.get('PORT', 3306),
        'mysql_path': r'C:\Program Files\MySQL\MySQL Server 8.0\bin' if platform.system() == 'Windows' else '',
    }


def obtener_bin(nombre):
    """Obtiene la ruta del binario de MySQL según el sistema operativo."""
    creds = obtener_credenciales_mysql()
    if platform.system() == 'Windows':
        return os.path.join(creds['mysql_path'], nombre + '.exe')
    return shutil.which(nombre) or nombre


def _env_mysql(creds):
    """
    ─── CORRECCIÓN ──────────────────────────────────────────────────────────
    La versión anterior pasaba la contraseña con --password=xxxx como argumento
    de línea de comandos. En Linux/Unix eso la expone en `ps aux`, donde
    cualquier usuario del sistema puede verla.

    La solución es pasar la contraseña a través de la variable de entorno
    MYSQL_PWD. MySQL y mysqldump la leen automáticamente y nunca aparece
    en la lista de procesos.
    ─────────────────────────────────────────────────────────────────────────
    """
    env = os.environ.copy()
    env['MYSQL_PWD'] = creds['password']
    return env


def probar_conexion_mysql():
    """Prueba la conexión a MySQL."""
    creds = obtener_credenciales_mysql()
    try:
        cmd = [
            obtener_bin('mysql'),
            '-h', creds['host'],
            '-u', creds['user'],
            '-P', str(creds['port']),
            '-e', 'SELECT 1;',
            creds['database'],
        ]
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            env=_env_mysql(creds),   # ← contraseña por variable de entorno
        )
        return resultado.returncode == 0
    except Exception:
        return False


# ========== VISTA PARA MOSTRAR OPCIONES DE RESPALDO ==========

@superadmin_required
@require_http_methods(["GET", "POST"])
def backup(request):
    """Muestra el menú de opciones para respaldo y restauración."""
    if request.method == "POST":
        accion = request.POST.get('accion')
        try:
            if accion == 'backup_completo':
                if not probar_conexion_mysql():
                    return JsonResponse(
                        {'error': 'No se puede conectar a MySQL. Verifica que el servidor esté en ejecución y que el usuario y contraseña sean válidos.'},
                        status=400
                    )
                return realizar_respaldo_completo()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    mysql_ok = probar_conexion_mysql()
    context = {
        'titulo':          'Respaldo y Restauración de Base de Datos',
        'mysql_conectado': mysql_ok,
    }
    return render(request, 'backup/menu.html', context)


# ========== VISTA PARA RESTAURAR DATOS ==========

@superadmin_required
@require_http_methods(["GET", "POST"])
def restaurar_datos(request):
    """Restaura datos desde un archivo SQL."""
    if 'archivo' not in request.FILES:
        return JsonResponse({'error': 'No se proporcionó archivo.'}, status=400)

    archivo = request.FILES['archivo']

    try:
        if not archivo.name.endswith('.sql'):
            return JsonResponse({'error': 'El archivo debe tener extensión .sql'}, status=400)

        contenido_sql = archivo.read().decode('utf-8')
        restaurar_bd_desde_sql(contenido_sql)

        return JsonResponse({'exito': True, 'mensaje': 'Base de datos restaurada correctamente.'})
    except Exception as e:
        return JsonResponse({'error': f'Error al restaurar: {str(e)}'}, status=400)


# ========== FUNCIONES DE RESPALDO ==========

def realizar_respaldo_completo():
    """Realiza un respaldo completo (estructura + datos)."""
    creds = obtener_credenciales_mysql()
    try:
        cmd = [
            obtener_bin('mysqldump'),
            '-h', creds['host'],
            '-u', creds['user'],
            '-P', str(creds['port']),
            creds['database'],
        ]
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=_env_mysql(creds),   # ← contraseña por variable de entorno
        )

        if resultado.returncode != 0:
            raise Exception(f"Error mysqldump: {resultado.stderr}")

        sql_content = resultado.stdout
        if not sql_content.strip():
            raise Exception("El respaldo está vacío.")

        sql_content = (
            f"-- Respaldo Completo de {creds['database']}\n"
            f"-- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"-- Tipo: Completo (Estructura + Datos)\n\n"
            + sql_content
        )
        return generar_archivo_descarga(sql_content, 'backup_completo')

    except subprocess.TimeoutExpired:
        raise Exception("Timeout al ejecutar mysqldump.")
    except Exception as e:
        raise Exception(f"Error en respaldo completo: {str(e)}")


# ========== FUNCIONES PARA RESTAURAR ==========

def restaurar_bd_desde_sql(contenido_sql):
    """Restaura la BD ejecutando el SQL recibido."""
    creds = obtener_credenciales_mysql()
    try:
        cmd = [
            obtener_bin('mysql'),
            '-h', creds['host'],
            '-u', creds['user'],
            '-P', str(creds['port']),
            creds['database'],
        ]
        proceso = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=_env_mysql(creds),   # ← contraseña por variable de entorno
        )
        stdout, stderr = proceso.communicate(input=contenido_sql, timeout=120)

        if proceso.returncode != 0:
            raise Exception(f"Error MySQL: {stderr}")
        return True

    except subprocess.TimeoutExpired:
        raise Exception("Timeout al restaurar la base de datos.")
    except Exception as e:
        raise Exception(f"Error al restaurar: {str(e)}")


# ========== FUNCIÓN PARA GENERAR DESCARGA ==========

def generar_archivo_descarga(contenido_sql, nombre_archivo):
    """Genera un archivo SQL para descargar."""
    response = HttpResponse(contenido_sql.encode('utf-8'), content_type='application/sql')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}_{timestamp}.sql"'
    return response