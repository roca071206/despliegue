"""Vista principal del sistema"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from app.decorators import admin_login_required
from app.context_processors import notificaciones
from ...models import Producto, Cliente, Venta, Proveedor, Compra, Reporte


@method_decorator(admin_login_required, name='dispatch')
class IndexView(View):
    def get(self, request):
        try:
            total_productos  = Producto.objects.count()
            total_clientes   = Cliente.objects.count()
            total_ventas     = Venta.objects.count()
            total_proveedores = Proveedor.objects.count()
            total_compras    = Compra.objects.count()
            total_reportes   = Reporte.objects.count()
        except Exception:
            total_productos = total_clientes = total_ventas = 0
            total_proveedores = total_compras = total_reportes = 0

        return render(request, 'Inicio/index.html', {
            'total_productos':  total_productos,
            'total_clientes':   total_clientes,
            'total_ventas':     total_ventas,
            'total_proveedores': total_proveedores,
            'total_compras':    total_compras,
            'total_reportes':   total_reportes,
        })


index = IndexView.as_view()


@admin_login_required
def notificaciones_data(request):
    """
    Endpoint simple para refrescar la campana sin recargar la página.
    """
    data = notificaciones(request)
    lista = data.get('notificaciones', [])[:20]
    payload = []
    for n in lista:
        payload.append({
            'tipo': n.get('tipo', 'info'),
            'icono': n.get('icono', '🔔'),
            'mensaje': n.get('mensaje', ''),
            'url': n.get('url', '#'),
            'prioridad': n.get('prioridad', 4),
            'notif_id': n.get('notif_id', None),
        })

    return JsonResponse({
        'ok': True,
        'total_notificaciones': data.get('total_notificaciones', 0),
        'notificaciones': payload,
    })


@login_required
def limpiar_notificaciones(request):
    """
    Elimina TODAS las notificaciones del usuario (leídas y no leídas).
    """
    from app.models import NotificacionEmail

    if request.method == 'POST':
        total_eliminadas = NotificacionEmail.objects.filter(
            usuario=request.user
        ).delete()[0]

        return JsonResponse({
            'ok': True,
            'mensaje': f'{total_eliminadas} notificaciones eliminadas',
            'eliminadas': total_eliminadas
        })

    return JsonResponse({
        'ok': False,
        'error': 'Método no permitido'
    }, status=405)


@login_required
def marcar_leida_notificacion(request, id):
    """
    Marca una notificación específica como leída.
    """
    from django.shortcuts import get_object_or_404
    from app.models import NotificacionEmail

    if request.method == 'POST':
        notif = get_object_or_404(NotificacionEmail, id=id, usuario=request.user)
        notif.leida = True
        notif.save()
        return JsonResponse({'ok': True, 'mensaje': 'Notificación marcada como leída'})
    
    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


@login_required
def eliminar_notificacion(request, id):
    """
    Elimina una notificación específica.
    """
    from django.shortcuts import get_object_or_404
    from app.models import NotificacionEmail

    if request.method == 'POST':
        notif = get_object_or_404(NotificacionEmail, id=id, usuario=request.user)
        notif.delete()
        return JsonResponse({'ok': True, 'mensaje': 'Notificación eliminada'})
    
    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)