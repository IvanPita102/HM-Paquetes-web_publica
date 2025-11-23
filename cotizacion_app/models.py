from django.db import models

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True, null=False)

    def __str__(self):
        return f"Servicio: -> {self.nombre} (Activo: {self.activo})"
    
class Cotizacion(models.Model):
    servicios = models.ManyToManyField(Servicio,verbose_name="Servicios Solicitados")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    nombre_cliente = models.CharField(max_length=100)
    email = models.EmailField()
    detalles_adicionales = models.TextField(blank=True, null=True)
    atendido = models.BooleanField(default=False)

    def __str__(self):
        nombres_servicios = ', '.join(self.servicios.all().values_list('nombre', flat=True))
        return f"Cotizacion del cliente: ->{self.servicio.nombre} Fecha: -> {self.fecha_solicitud} Servicios: -> {nombres_servicios} (Atendico: {self.atendido})"