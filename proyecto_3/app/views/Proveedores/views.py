"""Vistas para gestión de proveedores"""
import re
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from app.decorators import admin_login_required
from ...models import Proveedor


def _validar_proveedor(nombre, telefono, email, envio, proveedor_id=None):
    errores = []
    if not nombre:
        errores.append('El nombre es obligatorio.')
    elif len(nombre) < 3:
        errores.append('El nombre debe tener al menos 3 caracteres.')
    elif not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]+$', nombre):
        errores.append('El nombre solo puede contener letras y espacios.')

    if not telefono:
        errores.append('El teléfono es obligatorio.')
    elif not telefono.isdigit():
        errores.append('El teléfono solo puede contener números.')
    elif len(telefono) < 7 or len(telefono) > 15:
        errores.append('El teléfono debe tener entre 7 y 15 dígitos.')

    patron_email = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not email:
        errores.append('El email es obligatorio.')
    else:
        if not re.match(patron_email, email):
            errores.append('El email no tiene un formato válido.')
        else:
            qs = Proveedor.objects.filter(email=email)
            if proveedor_id:
                qs = qs.exclude(id=proveedor_id)
            if qs.exists():
                errores.append('Ya existe un proveedor con ese email.')

    if not envio:
        errores.append('Los días de envío son obligatorios.')
    elif not envio.isdigit():
        errores.append('Los días de envío solo pueden contener números enteros.')
    elif int(envio) < 1:
        errores.append('Los días de envío deben ser al menos 1.')
    elif int(envio) > 30:
        errores.append('Los días de envío no pueden superar 30 días.')

    return errores


@method_decorator(admin_login_required, name='dispatch')
class ProveedoresView(View):
    def get(self, request):
        lista = Proveedor.objects.all()
        busqueda = request.GET.get('busqueda', '').strip()
        envio_filtro = request.GET.get('envio', '').strip()
        fecha_desde = request.GET.get('fecha_desde', '').strip()
        fecha_hasta = request.GET.get('fecha_hasta', '').strip()

        if busqueda:
            lista = lista.filter(nombre__icontains=busqueda)

        if envio_filtro == 'rapido':
            lista = lista.filter(envio__lte=7)
        elif envio_filtro == 'normal':
            lista = lista.filter(envio__gte=8, envio__lte=15)
        elif envio_filtro == 'lento':
            lista = lista.filter(envio__gt=15)

        if fecha_desde:
            try:
                desde_date = date.fromisoformat(fecha_desde)
                lista = lista.filter(fechaRegistro__gte=desde_date)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                hasta_date = date.fromisoformat(fecha_hasta)
                lista = lista.filter(fechaRegistro__lte=hasta_date)
            except ValueError:
                pass

        return render(request, 'proveedores/proveedores.html', {
            'proveedores': lista,
            'busqueda': busqueda,
            'envio_filtro': envio_filtro,
        })


@method_decorator(admin_login_required, name='dispatch')
class CrearProveedorView(View):
    def post(self, request):
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        envio = request.POST.get('envio', '').strip()
        errores = _validar_proveedor(nombre, telefono, email, envio)
        if errores:
            for e in errores: messages.error(request, e)
        else:
            try:
                Proveedor.objects.create(nombre=nombre, telefono=telefono, email=email, envio=int(envio))
                messages.success(request, f'Proveedor "{nombre}" creado exitosamente.')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        return redirect('proveedores')


@method_decorator(admin_login_required, name='dispatch')
class EditarProveedorView(View):
    def post(self, request, id):
        proveedor = get_object_or_404(Proveedor, id=id)
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        envio = request.POST.get('envio', '').strip()
        errores = _validar_proveedor(nombre, telefono, email, envio, proveedor_id=id)
        if errores:
            for e in errores: messages.error(request, e)
        else:
            try:
                proveedor.nombre = nombre; proveedor.telefono = telefono
                proveedor.email = email; proveedor.envio = int(envio)
                proveedor.save()
                messages.success(request, f'Proveedor "{nombre}" actualizado exitosamente.')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        return redirect('proveedores')


@method_decorator(admin_login_required, name='dispatch')
class EliminarProveedorView(View):
    def post(self, request, id):
        proveedor = get_object_or_404(Proveedor, id=id)
        try:
            nombre = proveedor.nombre
            proveedor.delete()
            messages.success(request, f'Proveedor "{nombre}" eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('proveedores')


@method_decorator(admin_login_required, name='dispatch')
class ProveedoresJsonView(View):
    def get(self, request):
        lista = list(Proveedor.objects.all().values('id', 'nombre', 'telefono', 'email', 'envio', 'fechaRegistro'))
        return JsonResponse({'proveedores': lista})


proveedores        = ProveedoresView.as_view()
crear_proveedor    = CrearProveedorView.as_view()
editar_proveedor   = EditarProveedorView.as_view()
eliminar_proveedor = EliminarProveedorView.as_view()
proveedores_json   = ProveedoresJsonView.as_view()