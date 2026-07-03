"""
Servicio de notificaciones por email.
Envía notificaciones a usuarios activos (logged in).
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from app.models import NotificacionEmail


def enviar_notificacion_email(usuario, asunto, mensaje, tipo='info'):
    """
    Envía una notificación por email a un usuario.

    Args:
        usuario: Usuario Django
        asunto: Asunto del email
        mensaje: Cuerpo del mensaje
        tipo: Tipo de notificación (alerta, info, error, success)
    """
    if not usuario.email:
        return False

    # Crear notificación en BD
    notif = NotificacionEmail.objects.create(
        usuario=usuario,
        asunto=asunto,
        mensaje=mensaje,
        tipo=tipo,
    )

    # Intentar enviar email
    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
        notif.enviada = True
        notif.fecha_envio = timezone.now()
        notif.save()
        return True
    except Exception as e:
        print(f"Error enviando email a {usuario.email}: {e}")
        return False


def enviar_notificacion_a_activos(asunto, mensaje, tipo='info', excluir_usuario=None):
    """
    Envía una notificación a todos los usuarios activos (is_active=True).

    Args:
        asunto: Asunto del email
        mensaje: Cuerpo del mensaje
        tipo: Tipo de notificación
        excluir_usuario: Usuario a excluir (opcional)
    """
    usuarios = User.objects.filter(is_active=True)
    if excluir_usuario is not None:
        usuarios = usuarios.exclude(pk=excluir_usuario.pk)

    resultado = []
    for usuario in usuarios:
        enviada = enviar_notificacion_email(usuario, asunto, mensaje, tipo)
        resultado.append({
            'usuario': usuario.username,
            'enviada': enviada,
        })

    return resultado


def notificacion_stock_bajo(producto):
    """
    Envía notificación de stock bajo a todos los usuarios activos.
    """
    asunto = f"⚠️ Stock bajo: {producto.nombre}"
    if producto.stock == 0:
        mensaje = f"El producto '{producto.nombre}' está AGOTADO. Reabastecer urgentemente."
        tipo = 'error'
    else:
        mensaje = f"El producto '{producto.nombre}' tiene stock bajo ({producto.stock} unidades)."
        tipo = 'alerta'

    return enviar_notificacion_a_activos(asunto, mensaje, tipo)


def notificacion_compra_creada(compra):
    """
    Envía notificación cuando se crea una nueva compra.
    """
    producto_nombre = compra.Producto.nombre if compra.Producto else 'Producto sin asignar'
    asunto = f"Nueva compra: {producto_nombre}"
    mensaje = (
        f"Se ha registrado una nueva compra:\n"
        f"Proveedor: {compra.Proveedor.nombre}\n"
        f"Producto: {producto_nombre}\n"
        f"Cantidad: {compra.cantidad}\n"
        f"Total: ${compra.total:,.2f}\n"
        f"Estado: {compra.estado}"
    )
    tipo = 'info'

    return enviar_notificacion_a_activos(asunto, mensaje, tipo, excluir_usuario=compra.usuario)


def notificacion_venta_completada(venta):
    """
    Envía notificación cuando se completa una venta.
    """
    asunto = f"Venta completada: {venta.cliente}"
    mensaje = (
        f"Se ha completado la siguiente venta:\n"
        f"Cliente: {venta.cliente}\n"
        f"Total: ${venta.total:,.2f}\n"
        f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}"
    )
    tipo = 'success'

    return enviar_notificacion_a_activos(asunto, mensaje, tipo)


def notificacion_compra_proxima_vencer(compra):
    """
    Envía notificación de compra próxima a vencer.
    """
    producto_nombre = compra.Producto.nombre if compra.Producto else 'Producto sin asignar'
    dias_restantes = (compra.fechaCompra - timezone.now().date()).days

    if dias_restantes <= 0:
        asunto = f"🚨 Compra vencida: {producto_nombre}"
        mensaje = f"La compra '{producto_nombre}' del proveedor {compra.Proveedor.nombre} venció hace {abs(dias_restantes)} días."
        tipo = 'error'
    else:
        asunto = f"⏰ Compra próxima a vencer: {producto_nombre}"
        mensaje = f"La compra '{producto_nombre}' del proveedor {compra.Proveedor.nombre} vence en {dias_restantes} día(s)."
        tipo = 'alerta'

    return enviar_notificacion_a_activos(asunto, mensaje, tipo)
