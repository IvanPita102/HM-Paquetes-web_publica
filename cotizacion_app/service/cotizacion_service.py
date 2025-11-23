from django.db import transaction
from cotizacion_app.models import Cotizacion, Servicio

class ServicioCotizacion:
    @staticmethod
    def obtener_cotizacion(datos):
        # Lógica para obtener la cotización basada en los datos proporcionados
        pass
    
    @staticmethod
    @transaction.atomic
    def insertar_cotizacion(datos):
        """
        Inserta una nueva cotización con transacciones atómicas.
        No se crea la cotización si no se puede asociar al menos un servicio.
        """
        # Validar que se haya proporcionado un servicio
        servicio_id = datos.get('servicios')
        if not servicio_id:
            raise ValueError("No se puede crear una cotización sin servicios asociados")
        
        # Validar que el servicio exista antes de crear la cotización
        try:
            servicio = Servicio.objects.get(pk=servicio_id)
        except Servicio.DoesNotExist:
            raise ValueError(f"El servicio con ID {servicio_id} no existe")
        
        # Crear la cotización dentro de la transacción
        cotizacion = Cotizacion.objects.create(
            nombre_cliente=datos['nombre'],
            email=datos['email'],
            detalles_adicionales=datos.get('descripcion', ''),
        )
        
        # Asignar el servicio a la relación ManyToMany
        # Si esto falla, la transacción se revertirá y la cotización no se creará
        cotizacion.servicios.add(servicio)
        
        return cotizacion
    
    @staticmethod
    def listar_servicios_activos():
        return Servicio.objects.filter(activo=True)