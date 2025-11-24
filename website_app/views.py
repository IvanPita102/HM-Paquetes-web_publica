import logging
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from hmpaquetesapp.models import Envio, ItemDocumento, Locacion
from cotizacion_app.service.cotizacion_service import ServicioCotizacion
from cotizacion_app.models import Servicio, Cotizacion

logger = logging.getLogger(__name__)

def index(request):
    servicios = Servicio.objects.filter(activo=True)
    contexto = {
        'servicios': servicios,
    }
    return render(request, 'website_app/index.html', contexto) 

def about(request):
    return render(request, 'website_app/about.html') 

def services(request):
    return render(request, 'website_app/service.html') 

def goods_storage(request):
    return render(request, 'website_app/goods_storage.html')
    
def air_freight_service(request):
    return render(request, 'website_app/air_freight_service.html')

def land_transport_service(request):
    return render(request, 'website_app/land_transport_service.html')

def sea_freight_service(request):
    return render(request, 'website_app/sea_freight_service.html')

def contact(request):
    return render(request, 'website_app/contact.html')

def shipment_details(request, cod):
    """
    Obtiene el historial de un envío (Envio) buscando sus ItemsDocumento
    y utilizando la GenericForeignKey (item.documento) para cargar el documento asociado.
    """
    try:
        logger.info(f'Intentando obtener historial para el código: {cod}')
        
        envio_obj = Envio.objects.get(no_envio__iexact=cod)
        
        items = ItemDocumento.objects.filter(envio=envio_obj).select_related('documento_type').order_by('pk')
        
        logger.info(f'Items de documento encontrados: {items.count()}')
        
        if not items.exists():
            # Calcular días para entrega
            dias_para_entrega = 0
            if envio_obj.estado == 'Recibido':
                # envio_obj.locacion es un string, necesitamos buscar el objeto Locacion
                locacion_obj = None
                if envio_obj.locacion:
                    try:
                        locacion_obj = Locacion.objects.get(nombre=envio_obj.locacion)
                    except Locacion.DoesNotExist:
                        pass
                
                if locacion_obj and locacion_obj.es_almacen_central:
                    dias_para_entrega = 7
                else:
                    dias_para_entrega = 5
            elif envio_obj.estado == 'Enviado':
                dias_para_entrega = 1
            
            # Obtener URL de foto de forma segura
            foto_url = ''
            if envio_obj.estado == 'Entregado' and envio_obj.foto_entrega:
                try:
                    foto_url = envio_obj.foto_entrega.url
                except (AttributeError, ValueError):
                    foto_url = ''
            
            return JsonResponse({ 
                'success': True, 
                'envio': {
                    'codigo': envio_obj.no_envio,
                    'estado': envio_obj.estado,
                    'almacen': envio_obj.locacion if envio_obj.estado != 'No Recibido' and envio_obj.locacion else '',
                    'dias_para_entrega': dias_para_entrega,
                    'foto_confirmacion': foto_url,
                },
                'historial': [], 
                'mensaje': 'No se encontraron movimientos para este envío.' 
            }, safe=False)

        historial = []
        # Inicializar variables por si el loop no procesa ningún item
        fecha = None
        tipo = None
        
        for item in items:
            doc = item.documento 
            
            if doc is None:
                logger.info(f"Advertencia: Documento no resuelto para ItemDocumento ID: {item.id}. Omitiendo item.")
                continue

            # datos básicos
            tipo = item.documento_type.model
            evento = "Desconocido"
            detalle = ""
            
            # Usamos getattr de forma segura
            fecha_dt = getattr(doc, 'fecha_creacion', None)
            fecha = fecha_dt.strftime('%d/%m/%Y %I:%M %p') if fecha_dt else 'N/A'

            if tipo == 'entradarecibida':
                evento = "Entrada"
                locacion_nombre = getattr(getattr(doc, 'locacion_origen', None), 'nombre', 'Desconocida')
                detalle = f"""Se da entrada al envío en el almacén <strong>{locacion_nombre}</strong>"""

            elif tipo == 'transferenciaalmacen':
                evento = "Transferencia"
                locacion_origen_nombre = getattr(getattr(doc, 'locacion_origen', None), 'nombre', 'Desconocido')
                locacion_destino_nombre = getattr(getattr(doc, 'locacion_destino', None), 'nombre', 'Desconocido')

                detalle = f"""El envio a arribado al almacén <strong>{locacion_destino_nombre}</strong> transferido desde el almacén <strong>{locacion_origen_nombre}</strong>."""

            elif tipo == 'despachomensajero':
                locacion_origen_nombre = getattr(getattr(doc, 'locacion_origen', None), 'nombre', 'Desconocido')
                base_detalle = f"""El mensajero recogio el envio en el centro de distribucion <strong>{locacion_origen_nombre}</strong> y esta en proceso de entrega."""
                
                if item.devuelto:
                    evento = "Devolución"
                    detalle = base_detalle + "<br><br>El envío no fue entregado y se retorna al centro de distribucion."
                elif item.confirmado:
                    evento = "Entrega Exitosa"
                    detalle = "Su envío fue entregado satisfactoriamente."
                else:
                    evento = "Despachado a Mensajero"
                    detalle = base_detalle
                

            # Agregar el evento al historial
            historial.append({
                'evento': evento,
                'fecha': fecha,
                'detalle': detalle,
                'tipo': tipo
            })

        if len(historial) == 0:
            evento = 'Aduana'
            detalle = 'El envío aún no ha sido recibido por el transportista.' if envio_obj.estado in ['No Recibido', 'Desaforado'] else f'Estado {envio_obj.estado} incorrecto.'
            # Usar fecha actual si no hay fecha disponible
            fecha_fallback = timezone.now().strftime('%d/%m/%Y %I:%M %p')
            tipo_fallback = 'sin_tipo'
        
            historial.append({
                'evento': evento,
                'fecha': fecha if fecha else fecha_fallback,
                'detalle': detalle,
                'tipo': tipo if tipo else tipo_fallback
            })

        # Ordenar historial (usando la fecha como cadena formateada)
        historial.sort(key=lambda x: x['fecha'] or '', reverse=True)
        
        # logica para el calculo de dias para entrega
        dias_para_entrega = 0
        if envio_obj.estado == 'Recibido':
            # envio_obj.locacion es un string, necesitamos buscar el objeto Locacion
            locacion_obj = None
            if envio_obj.locacion:
                try:
                    locacion_obj = Locacion.objects.get(nombre=envio_obj.locacion)
                except Locacion.DoesNotExist:
                    pass
            
            if locacion_obj and locacion_obj.es_almacen_central:
                dias_para_entrega = 7
            else:
                dias_para_entrega = 5

        elif envio_obj.estado == 'Enviado':
            dias_para_entrega = 1

        logger.info(f'Historial completo para {cod}: {historial}')
        logger.info(f'Foto de entrega: {envio_obj.foto_entrega}')
        
        # Obtener URL de foto de forma segura
        foto_url = ''
        if envio_obj.estado == 'Entregado' and envio_obj.foto_entrega:
            try:
                foto_url = envio_obj.foto_entrega.url
            except (AttributeError, ValueError):
                foto_url = ''
        
        return JsonResponse({
            'success': True, 
            'envio': {
                'codigo': envio_obj.no_envio,
                'estado': envio_obj.estado,
                'almacen': envio_obj.locacion if envio_obj.estado != 'No Recibido' else '',
                'dias_para_entrega': dias_para_entrega,
                'foto_confirmacion': foto_url,
            },
            'historial': historial, 
            }, safe=False)
    
    except Envio.DoesNotExist:
        # Manejar el caso de que el envío no exista
        return JsonResponse({ 'success': False, 'error': f'Envío con código {cod} no encontrado'}, status=404)
        
    except Exception as e:
        # Capturar cualquier otro error que pueda ocurrir durante el procesamiento
        error_msg = f'Ocurrió un error interno: {str(e)}'
        logger.error(f"Error en shipment_details: {error_msg}")
        return JsonResponse({ 'success': False, 'error': error_msg}, status=500)

def insertar_cotizacion(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        datos = {
            'nombre': request.POST.get('nombre'),
            'email': request.POST.get('correo'),  # El formulario envía 'correo', no 'email'
            'servicios': request.POST.get('servicios'),
            'descripcion': request.POST.get('descripcion')    
        }
        
        # Validar campos requeridos
        if not datos['nombre'] or not datos['email']:
            return JsonResponse({'error': 'El nombre y el email son requeridos'}, status=400)
        
        cotizacion = ServicioCotizacion.insertar_cotizacion(datos)
        
        return JsonResponse({
            'success': True,
            'message': 'Cotización creada exitosamente',
            'cotizacion_id': cotizacion.id
        }, status=201)
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Ocurrió un error al procesar la cotización'}, status=500)