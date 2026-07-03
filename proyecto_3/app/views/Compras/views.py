"""Vistas para gestión de compras — CORREGIDO: usa request.user directamente"""
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.db import transaction
from django.http import JsonResponse
from app.decorators import admin_login_required
from app.services.notifications import notificacion_stock_bajo, notificacion_compra_creada, notificacion_compra_proxima_vencer
from ...models import Compra, Proveedor, Producto


# ─────────────────────────────────────────────
# Helpers de stock
# ─────────────────────────────────────────────

def _sumar_stock(producto_id, cantidad):
    """Aumenta el stock del producto. Llamar dentro de transaction.atomic()."""
    producto = Producto.objects.select_for_update().get(pk=producto_id)
    producto.stock += cantidad
    producto.save()


def _restar_stock(producto_id, cantidad):
    """Reduce el stock del producto. Llamar dentro de transaction.atomic()."""
    producto = Producto.objects.select_for_update().get(pk=producto_id)
    producto.stock = max(0, producto.stock - cantidad)
    producto.save()
    # Notificar si stock queda bajo
    if producto.stock <= 5:
        notificacion_stock_bajo(producto)


# ─────────────────────────────────────────────
# Helpers de validación
# ─────────────────────────────────────────────

def _validar_fecha_nueva(fecha_str):
    try:
        fecha = date.fromisoformat(fecha_str)
    except ValueError:
        return None, 'La fecha no tiene un formato válido.'
    hoy    = date.today()
    limite = hoy + timedelta(days=7)
    if fecha < hoy:
        return None, f'La fecha no puede ser anterior a hoy ({hoy.strftime("%d/%m/%Y")}).'
    if fecha > limite:
        return None, f'La fecha no puede ser mayor a 7 días desde hoy ({limite.strftime("%d/%m/%Y")}).'
    return fecha, None


def _validar_fecha_editar(fecha_str):
    try:
        return date.fromisoformat(fecha_str), None
    except ValueError:
        return None, 'La fecha no tiene un formato válido.'


def _validar_cantidad_precio(cantidad_str, precio_str):
    """Valida y convierte cantidad y precio. Retorna (cantidad_int, precio_float, error)."""
    if not cantidad_str.isdigit() or int(cantidad_str) < 1:
        return None, None, 'La cantidad debe ser un número entero mayor a 0.'
    try:
        precio = float(precio_str.replace(',', '.'))
        if precio <= 0:
            raise ValueError
    except ValueError:
        return None, None, 'El precio debe ser un número mayor a 0.'
    return int(cantidad_str), precio, None


# ─────────────────────────────────────────────
# Vistas
# ─────────────────────────────────────────────

@method_decorator(admin_login_required, name='dispatch')
class ComprasView(View):
    def get(self, request):
        hoy           = date.today()
        lista_compras = Compra.objects.select_related(
            'usuario', 'Producto', 'Proveedor'
        ).all().order_by('-fechaCompra')

        busqueda = request.GET.get('busqueda', '').strip()
        if busqueda:
            lista_compras = (
                lista_compras.filter(Proveedor__nombre__icontains=busqueda) |
                lista_compras.filter(Producto__nombre__icontains=busqueda)
            )

        estado_filtro = request.GET.get('estado', '').strip()
        if estado_filtro in ('Completada', 'Pendiente'):
            lista_compras = lista_compras.filter(estado=estado_filtro)

        fecha_desde = request.GET.get('fecha_desde', '').strip()
        fecha_hasta = request.GET.get('fecha_hasta', '').strip()

        if fecha_desde:
            try:
                desde_date = date.fromisoformat(fecha_desde)
                lista_compras = lista_compras.filter(fechaCompra__gte=desde_date)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                hasta_date = date.fromisoformat(fecha_hasta)
                lista_compras = lista_compras.filter(fechaCompra__lte=hasta_date)
            except ValueError:
                pass

        return render(request, 'Compras/Compras.html', {
            'compras':     lista_compras,
            'proveedores': Proveedor.objects.all(),
            'productos':   Producto.objects.all(),
            'fecha_min':   hoy.strftime('%Y-%m-%d'),
            'fecha_max':   (hoy + timedelta(days=7)).strftime('%Y-%m-%d'),
        })


@method_decorator(admin_login_required, name='dispatch')
class CrearCompraView(View):
    def post(self, request):
        fecha_str    = request.POST.get('fecha', '').strip()
        estado_str   = request.POST.get('estado', 'Pendiente').strip()
        producto_id  = request.POST.get('producto_id', '').strip()
        proveedor_id = request.POST.get('proveedor_id', '').strip()
        cantidad_str = request.POST.get('cantidad', '').strip()
        precio_str   = request.POST.get('precio_unitario', '').strip()

        if not fecha_str or not producto_id or not proveedor_id:
            messages.error(request, 'Fecha, producto y proveedor son obligatorios.')
            return redirect('compras')

        fecha, error = _validar_fecha_nueva(fecha_str)
        if error:
            messages.error(request, error)
            return redirect('compras')

        cantidad, precio, error = _validar_cantidad_precio(cantidad_str, precio_str)
        if error:
            messages.error(request, error)
            return redirect('compras')

        try:
            with transaction.atomic():
                compra = Compra.objects.create(
                    fechaCompra     = fecha,
                    estado          = estado_str,
                    cantidad        = cantidad,
                    precio_unitario = precio,
                    usuario         = request.user,   # ← CORRECCIÓN: usa auth.User directamente
                    Producto_id     = int(producto_id),
                    Proveedor_id    = int(proveedor_id),
                )
                if estado_str == 'Completada':
                    _sumar_stock(int(producto_id), cantidad)

            # Enviar notificación de nueva compra
            notificacion_compra_creada(compra)
            messages.success(request, f'Compra #{compra.idCompra} registrada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al crear la compra: {str(e)}')
        return redirect('compras')


@method_decorator(admin_login_required, name='dispatch')
class EditarCompraView(View):
    def post(self, request, id):
        compra = get_object_or_404(Compra, idCompra=id)

        fecha_str    = request.POST.get('fecha', '').strip()
        estado_nuevo = request.POST.get('estado', 'Pendiente').strip()
        producto_id  = request.POST.get('producto_id', '').strip()
        proveedor_id = request.POST.get('proveedor_id', '').strip()
        cantidad_str = request.POST.get('cantidad', '').strip()
        precio_str   = request.POST.get('precio_unitario', '').strip()

        if not fecha_str or not producto_id or not proveedor_id:
            messages.error(request, 'Fecha, producto y proveedor son obligatorios.')
            return redirect('compras')

        fecha, error = _validar_fecha_editar(fecha_str)
        if error:
            messages.error(request, error)
            return redirect('compras')

        cantidad_nueva, precio_nuevo, error = _validar_cantidad_precio(cantidad_str, precio_str)
        if error:
            messages.error(request, error)
            return redirect('compras')

        try:
            with transaction.atomic():
                estado_anterior   = compra.estado
                producto_anterior = compra.Producto_id
                cantidad_anterior = compra.cantidad
                producto_nuevo    = int(producto_id)

                if estado_anterior == 'Completada' and producto_anterior:
                    _restar_stock(producto_anterior, cantidad_anterior)

                if estado_nuevo == 'Completada':
                    _sumar_stock(producto_nuevo, cantidad_nueva)

                compra.fechaCompra     = fecha
                compra.estado          = estado_nuevo
                compra.cantidad        = cantidad_nueva
                compra.precio_unitario = precio_nuevo
                compra.usuario         = request.user   # ← CORRECCIÓN
                compra.Producto_id     = producto_nuevo
                compra.Proveedor_id    = int(proveedor_id)
                compra.save()

            messages.success(request, f'Compra #{compra.idCompra} actualizada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')
        return redirect('compras')


@method_decorator(admin_login_required, name='dispatch')
class EliminarCompraView(View):
    def post(self, request, id):
        compra = get_object_or_404(Compra, idCompra=id)
        try:
            with transaction.atomic():
                if compra.estado == 'Completada' and compra.Producto_id:
                    _restar_stock(compra.Producto_id, compra.cantidad)
                compra_id = compra.idCompra
                compra.delete()
            messages.success(request, f'Compra #{compra_id} eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')
        return redirect('compras')


@method_decorator(admin_login_required, name='dispatch')
class ComprasJsonView(View):
    def get(self, request):
        lista = [
            {
                'id':              c.idCompra,
                'fecha':           str(c.fechaCompra),
                'estado':          c.estado,
                'cantidad':        c.cantidad,
                'precio_unitario': float(c.precio_unitario),
                'total':           float(c.total),
                'usuario':         c.usuario.get_full_name() or c.usuario.username if c.usuario else '',
                'producto':        c.Producto.nombre  if c.Producto  else '',
                'proveedor':       c.Proveedor.nombre if c.Proveedor else '',
            }
            for c in Compra.objects.select_related(
                'usuario', 'Producto', 'Proveedor'
            ).order_by('-fechaCompra')
        ]
        return JsonResponse({'compras': lista})


compras               = ComprasView.as_view()
crear_compra          = CrearCompraView.as_view()
modal_editar_compra   = EditarCompraView.as_view()
modal_eliminar_compra = EliminarCompraView.as_view()
compras_json          = ComprasJsonView.as_view()
