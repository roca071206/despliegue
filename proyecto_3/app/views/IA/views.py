from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import os

from app.models import Producto, Cliente, Venta, DetalleVenta, Compra, Proveedor


def obtener_contexto():
    try:
        productos = Producto.objects.select_related('idMarca', 'idTipo', 'idUnidad').all()[:30]
        lista_productos = "\n".join([
            f"- {p.nombre} | Marca: {p.idMarca.nombreMarca} | Tipo: {p.idTipo.nombre_tipo} | Stock: {p.stock} | Precio: ${p.precio}"
            for p in productos
        ])

        stock_bajo = Producto.objects.filter(stock__lte=5).values_list('nombre', 'stock')
        lista_stock_bajo = "\n".join([f"- {n}: {s} unidades" for n, s in stock_bajo]) or "Ninguno"

        clientes_activos   = Cliente.objects.filter(estado='activo').count()
        clientes_inactivos = Cliente.objects.filter(estado='inactivo').count()

        ventas_completadas = Venta.objects.filter(estado='Completada').count()
        ventas_pendientes  = Venta.objects.filter(estado='Pendiente').count()
        from django.db.models import Sum
        total_vendido = Venta.objects.filter(estado='Completada').aggregate(t=Sum('total'))['t'] or 0

        ultimas_ventas = Venta.objects.all()[:5]
        lista_ventas = "\n".join([
            f"- Venta #{v.id} | Cliente: {v.cliente} | Total: ${v.total} | Estado: {v.estado}"
            for v in ultimas_ventas
        ])

        compras_completadas = Compra.objects.filter(estado='Completada').count()
        compras_pendientes  = Compra.objects.filter(estado='Pendiente').count()

        total_proveedores = Proveedor.objects.count()
        lista_proveedores = "\n".join([
            f"- {p.nombre} | Tel: {p.telefono}"
            for p in Proveedor.objects.all()[:10]
        ])

        return f"""Eres un asistente inteligente del Sistema de Inventario.
DEBES responder SIEMPRE en español, nunca en inglés.
Responde de forma clara y concisa.

=== PRODUCTOS (primeros 30) ===
{lista_productos}

=== PRODUCTOS CON STOCK BAJO (≤5 unidades) ===
{lista_stock_bajo}

=== CLIENTES ===
- Activos: {clientes_activos}
- Inactivos: {clientes_inactivos}

=== VENTAS ===
- Completadas: {ventas_completadas}
- Pendientes: {ventas_pendientes}
- Total vendido: ${total_vendido}

Últimas 5 ventas:
{lista_ventas}

=== COMPRAS ===
- Completadas: {compras_completadas}
- Pendientes: {compras_pendientes}

=== PROVEEDORES ({total_proveedores} en total) ===
{lista_proveedores}"""

    except Exception as e:
        return f"Eres un asistente de inventario. Responde SIEMPRE en español. Error al cargar datos: {str(e)}"


def ia_index(request):
    return render(request, 'IA/IA.html')


@csrf_exempt
def ia_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')

        contexto = obtener_contexto()

        GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

        headers = {
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json',
        }

        payload = {
            'model': 'llama-3.1-8b-instant',
            'messages': [
                {'role': 'system', 'content': contexto},
                {'role': 'user',   'content': user_message},
            ],
            'max_tokens': 512,
            'temperature': 0.5,
        }

        try:
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            result = response.json()

            if 'choices' not in result:
                return JsonResponse({'reply': str(result), 'status': 'error'})

            reply = result['choices'][0]['message']['content']
            return JsonResponse({'reply': reply, 'status': 'ok'})

        except Exception as e:
            return JsonResponse({'reply': f'Error con la IA: {str(e)}', 'status': 'error'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)