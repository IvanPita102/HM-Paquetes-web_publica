from django.db import models
from django.forms.models import model_to_dict
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import transaction
from django.contrib.contenttypes.fields import GenericRelation

# ----------------------------------------------------------------------
# 🛑 ATENCIÓN: Todos los modelos tienen ahora managed=False y db_table
# ----------------------------------------------------------------------

# Modelo para la gestión de provincias
class Provincia(models.Model):
    nombre = models.CharField(max_length=30, verbose_name="Nombre de la provincia")
    descripcion = models.CharField(max_length=250, verbose_name="Descripción de la provincia")
    codigo_aduana = models.CharField(max_length=10, unique=True, verbose_name="Código de aduana")

    def __str__(self):
        return f"{self.nombre} ({self.codigo_aduana})"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_provincia'


class Locacion(models.Model): 
    nombre = models.CharField(max_length=30, verbose_name="Nombre del almacen")
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT, 
        null=False,             
        blank=False,             
        related_name='locaciones',
        verbose_name="Provincia de ubicación"
    )
    permite_aforo = models.BooleanField(default=False, verbose_name='¿Permite desaforado?', help_text="Marca si permite desaforo")
    es_almacen_central = models.BooleanField(
        default=False,
        verbose_name="¿Es almacén central?",
        help_text="Marcar si es un almacén central"
    )    

    def __str__(self):
        return f"Id -> {self.pk } locacion {self.nombre} | es central ? { "Si" if self.es_almacen_central else "No" }"
    
    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_locacion'
    

# Modelo para la gestión de municipios
class Municipio(models.Model):
    nombre = models.CharField(max_length=30, verbose_name="Nombre del municipio")
    codigo_aduana = models.CharField(max_length=10, blank=True, null=True, verbose_name="Código de aduana")
    dpa = models.CharField(max_length=4, blank=True, null=True, verbose_name="Código DPA")
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.CASCADE,
        related_name='municipios',
        verbose_name="Provincia"
    )

    def __str__(self):
        return f"{self.nombre} ({self.codigo_aduana})"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_municipio'


# Modelo para domicilios
class Domicilio(models.Model):
    calle = models.CharField(max_length=255, blank=True,  null=True, verbose_name="Calle")
    entre_calle = models.CharField(max_length=255, blank=True, null=True, verbose_name="Entre calle")
    y_calle = models.CharField(max_length=255, blank=True, null=True, verbose_name="Y calle")
    no = models.CharField(max_length=255, blank=True, null=True, verbose_name="Número")
    piso = models.CharField(max_length=255, blank=True, null=True, verbose_name="Piso")
    apto = models.CharField(max_length=255, blank=True, null=True, verbose_name="Apartamento")
    codigo_provincia = models.CharField(max_length=255, verbose_name="Código de provincia")
    codigo_municipio = models.CharField(max_length=255, verbose_name="Código de municipio")
    direccion_completa = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección completa")

    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.CASCADE,
        related_name='domicilios',
        blank=True,
        null=True,
        to_field='codigo_aduana',
        db_column='provincia_codigo_aduana',
        verbose_name="Provincia"
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.CASCADE,
        related_name='domicilios',
        blank=True,
        null=True,
        db_column='municipio_codigo_aduana',
        verbose_name="Municipio"
    )

    def save(self, *args, **kwargs):
        # Asignar la provincia automáticamente si el código de provincia está presente
        if self.codigo_provincia:
            self.provincia = Provincia.objects.filter(codigo_aduana=self.codigo_provincia).first()
        
        # Asignar el municipio automáticamente si el código de municipio está presente y la provincia también
        if self.codigo_municipio and self.provincia:
            self.municipio = Municipio.objects.filter(codigo_aduana=self.codigo_municipio, provincia=self.provincia).first()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Domicilio: {self.direccion_completa}, {self.codigo_provincia}, {self.codigo_municipio}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_domicilio'


# Modelo de contacto asociado a un domicilio
class Contacto(models.Model):
    telefono = models.CharField(max_length=255, verbose_name="Teléfono")
    domicilio = models.ForeignKey(Domicilio, on_delete=models.CASCADE, related_name='contactos', verbose_name="Domicilio")

    def __str__(self):
        return f"Contacto: {self.telefono}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_contacto'

# Modelo de persona
class Persona(models.Model):
    primer_nombre = models.CharField(max_length=30, verbose_name="Primer nombre", db_index=True)
    segundo_nombre = models.CharField(max_length=30, blank=True, null=True, verbose_name="Segundo nombre", db_index=True)
    primer_apellido = models.CharField(max_length=30, verbose_name="Primer apellido", db_index=True)
    segundo_apellido = models.CharField(max_length=30, blank=True, null=True, verbose_name="Segundo apellido", db_index=True)
    nacionalidad = models.CharField(max_length=3, verbose_name="Nacionalidad")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento", blank=True, null=True)
    carnet_de_identificacion = models.CharField(max_length=30, db_index=True, unique=True, verbose_name="Carné de identidad")

    @property
    def nombre_completo(self):
        # Armar el nombre completo considerando que algunos campos pueden ser nulos o vacíos
        nombres = [self.primer_nombre]
        if self.segundo_nombre:
            nombres.append(self.segundo_nombre)
        
        apellidos = [self.primer_apellido]
        if self.segundo_apellido:
            apellidos.append(self.segundo_apellido)
        
        return " ".join(nombres + apellidos)

    def __str__(self):
        return f"{self.primer_nombre} {self.primer_apellido}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_persona'

# Modelo de destinatario, que asocia una persona y un contacto
class Destinatario(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='destinatarios', verbose_name="Persona")
    contacto = models.ForeignKey(Contacto, on_delete=models.CASCADE, related_name='destinatarios', verbose_name="Contacto")

    def __str__(self):
        return f"Destinatario: {self.persona} ({self.contacto})"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_destinatario'

# Modelo de manifiesto postal
class ManifiestoPostal(models.Model):
    operador = models.CharField(max_length=255, verbose_name="Operador")
    codigo_aduana = models.CharField(max_length=255, verbose_name="Código de aduana")
    agencia_origen = models.CharField(max_length=255, verbose_name="Agencia de origen")
    no_ga = models.CharField(max_length=255, verbose_name="Número GA")
    no_vuelo = models.CharField(max_length=255, verbose_name="Número de vuelo")
    fecha_arribo = models.DateField(verbose_name="Fecha de arribo" , null=True, blank=True)
    es_nacional = models.BooleanField(default=False, verbose_name="Es nacional ?")
    cantidad_bultos = models.IntegerField(verbose_name="Cantidad de bultos")
    facturado = models.BooleanField(default=False, verbose_name="Facturado")

    def __str__(self):
        return f"Manifiesto {self.no_ga} ({self.operador})"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_manifiestopostal'


# Modelo de envío, que se asocia a un destinatario y un manifiesto
class Envio(models.Model):
    no_envio = models.CharField(max_length=30, verbose_name="Número de envío", db_index=True)
    peso = models.FloatField(verbose_name="Peso")
    pais_origen_destino = models.CharField(max_length=3, verbose_name="País de origen/destino")
    descripcion = models.TextField(verbose_name="Descripción")
    fecha_imposicion = models.DateField(verbose_name="Fecha de imposición", null=True, blank=True)
    arancel = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    aranceles_pagados = models.BooleanField(verbose_name="Aranceles pagados", default=True)
    entrega_domicilio = models.BooleanField(verbose_name="Entrega a domicilio", default=False)
    fecha_recepcion = models.DateField(null=True, blank=True)
    locacion = models.CharField(max_length=100, verbose_name="Localización", null=True, blank=True)
    foto_entrega = models.ImageField(upload_to='entregas/', null=True, blank=True, verbose_name="Foto de la entrega")
    fecha_entrega = models.DateField(null=True, blank=True)
    
    # Nuevo campo estado con valores limitados y valor por defecto
    ESTADOS_CHOICES = [
        ('Desaforado','Desaforado'),
        ('No Recibido', 'No Recibido'),
        ('Recibido', 'Recibido'),
        ('Enviado', 'Enviado'),
        ('Entregado', 'Entregado'),
        ('En Trayecto', 'En Trayecto'),
    ]
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CHOICES,
        default='No Recibido',
        verbose_name="Estado",
        db_index=True
    )

    destinatario = models.ForeignKey(Destinatario, on_delete=models.CASCADE, related_name='envios', verbose_name="Destinatario")
    manifiesto = models.ForeignKey(ManifiestoPostal, on_delete=models.CASCADE, related_name='envios', verbose_name="Manifiesto postal")
    pago_mensajero = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Pago al mensajero", default=0)
    observacion = models.TextField(verbose_name="Observaciones", blank=True, default="")
    
    def calcular_pago_mensajero(self):
        """
        Calcula el pago al mensajero según el peso del envío.
        """
        PRECIO_BASE = 400  # Precio base por peso
        try:
            peso_kg = float(self.peso)  # Convertir el peso a float si es necesario
            peso_libras = peso_kg * 2.2  # Convertir de kg a libras
            if peso_libras <= 50:
                return PRECIO_BASE
            elif 50 < peso_libras <= 100:
                return PRECIO_BASE * 2
            elif 100 < peso_libras <= 150:
                return PRECIO_BASE * 2.5
            elif 150 < peso_libras <= 200:
                return PRECIO_BASE * 3
            else:
                return 0  # En caso de que el peso exceda los 200 libras, sin especificar
        except (ValueError, TypeError):
            # Si el peso no es válido, devuelve 0
            return 0

    def save(self, *args, **kwargs):
        # Calcular el pago al mensajero antes de guardar
        self.pago_mensajero = self.calcular_pago_mensajero()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Envío {self.no_envio} ({self.fecha_imposicion})"
    
    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_envio'
    

class Mensajero(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre del Chofer")
    carne_ident = models.CharField(max_length=30, verbose_name="Carné de Identidad", blank=True, null=True)
    telefono = models.CharField(max_length=30, verbose_name="Teléfono del Chofer", blank=True, null=True)
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, related_name='mensajero', null=True, blank=True)

    def __str__(self):
        return f"{self.name} - CI: {self.carne_ident}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_mensajero'

class Chofer(models.Model):
    chofer = models.CharField(max_length=255, verbose_name="Nombre del Chofer")
    carne_ident = models.CharField(max_length=20, verbose_name="Carné de Identidad", blank=True, null=True)
    telefono = models.CharField(max_length=15, verbose_name="Teléfono del Chofer", blank=True, null=True)
    datos_vehiculo = models.CharField(max_length=255, verbose_name="Datos del Vehículo", blank=True, null=True)
    matricula = models.CharField(max_length=20, verbose_name="Matrícula", blank=True, null=True)

    def __str__(self):
        return f"Nombre: {self.chofer} - CI: {self.carne_ident}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_chofer'

class ArchivoExportado(models.Model):
    archivo = models.FileField(upload_to='exportaciones_excel/')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archivos_exportados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    TIPOS_REPORTES = [
        ('Carga Recibida', 'Carga Recibida'),
        ('Carga Enviada a Provincia', 'Carga Enviada a Provincia'),
        ('Carga enviada entre Almacén', 'Carga enviada entre Almacén'),
    ]
    tipo_reporte = models.CharField(max_length=255, choices=TIPOS_REPORTES, default='cargas', verbose_name="Tipo de Reporte")

    def __str__(self):
        return f"{self.archivo.name} - {self.usuario.username}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_archivoexportado'


class TareaPendiente(models.Model):
    """
    Modelo para almacenar tareas pendientes de procesamiento
    Permitirá encolar peticiones para procesarlas posteriormente
    """
    TIPO_CHOICES = (
        ('marcar_entregado', 'Marcar Envío como Entregado'),
        # Agregar otros tipos de tareas según sea necesario
    )
    
    STATUS_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completada', 'Completada'),
        ('error', 'Error'),
    )
    
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    datos = models.JSONField(help_text="Datos necesarios para ejecutar la tarea")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    resultado = models.JSONField(null=True, blank=True)
    mensaje_error = models.TextField(null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_tareapendiente'
        verbose_name = "Tarea pendiente"
        verbose_name_plural = "Tareas pendientes"
        ordering = ['fecha_creacion']
    
    def __str__(self):
        return f"Tarea {self.tipo} - {self.estado} ({self.id})"


##########################################################################################################
class DocumentoBaseSimple(models.Model):
    locacion_origen = models.ForeignKey(
        Locacion,
        related_name='%(class)s_origen', 
        on_delete=models.CASCADE,
        verbose_name="Almacén de origen"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=30, verbose_name="Nombre del usuario")

    class Meta:
        abstract = True


class DocumentoBase(DocumentoBaseSimple):
    mensajero = models.ForeignKey(
        Mensajero,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    chofer = models.ForeignKey(Chofer, on_delete=models.SET_NULL, null=True,blank=True)
    confirmado = models.BooleanField(default=False)

    class Meta:
        abstract = True     


class EntradaRecibida(DocumentoBaseSimple):
    
    def __str__(self):
        return f"Entradas recibida {self.pk} | {self.locacion_origen} → fecha {self.fecha_creacion}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_entradarecibida'

class TransferenciaAlmacen(DocumentoBase):
    locacion_destino = models.ForeignKey(
        Locacion, 
        related_name='transferencia',
        on_delete=models.CASCADE,
        verbose_name="Almacén destino"
    )
    items = GenericRelation('ItemDocumento', content_type_field='documento_type', object_id_field='documento_id')
    def __str__(self):
        return f"Transferencia {self.pk} | {self.locacion_origen.nombre} → {self.locacion_destino.nombre}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_transferenciaalmacen'

class DespachoMensajero(DocumentoBase):
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.CASCADE,
        verbose_name="Provincia destino"
    )
    
    def __str__(self):
        return f"Despacho {self.pk} | {self.locacion_origen.nombre} → {self.provincia.nombre} → {self.mensajero if self.mensajero else 'Sin mensajero'}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_despachomensajero'


class ItemDocumento(models.Model):
    documento_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ['transferenciaalmacen', 'despachomensajero','entradarecibida']}
    )
    documento_id = models.PositiveIntegerField()
    documento = GenericForeignKey('documento_type', 'documento_id')
    
    envio = models.ForeignKey(
        Envio, 
        on_delete=models.CASCADE,
        verbose_name="Código envío"
    )

    confirmado = models.BooleanField(default=False)

    # campo espeficico para manejar devoluciones en despachos 
    devuelto = models.BooleanField(
        default=False,
        verbose_name="Devuelto al almacen",
        help_text="Indica si el envio fue devuelto por el mensajero al almacen"
    )

    @property
    def es_despacho_mensajero(self):
        """Verifica si este item pertenece a un despacho a mensajero"""
        """
        Indica si el item pertenece a un despacho a mensajero.
        Returns:
            bool: True si pertenece a un despacho a mensajero, False en caso contrario.
        """
        return self.documento_type.model == 'despachomensajero'
    

    @transaction.atomic
    def marcar_como_devuelto(self):
        """Marca el envío como devuelto (solo válido para despachos)"""
        """
        Marca el envio como devuelto (solo valido para despachos a mensajeros).
        Cambia el estado del item y del envio asociado.
        Lanza un error si el item no pertenece a un despacho a mensajero.
        Raise:
            ValueError: si el item no es de un despacho a mensajero
        """     
        if not self.es_despacho_mensajero:
            raise ValueError("Solo se pueden devolver envíos de despachos a mensajeros")
        
        self.devuelto = True
        # Resetear confirmado
        self.confirmado = False  
        self.save()
        
        # Actualizar estado del envío
        self.envio.estado = 'Recibido'
        self.envio.save()


    def __str__(self):
        return f"Item {self.envio.no_envio} | Doc: {self.documento}"
    
    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_itemdocumento'

class Permiso(models.Model):
    idUser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permisos')
    idGroup = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='permisos')
    idPropiedad = models.ForeignKey('Propiedad', on_delete=models.CASCADE, related_name='permisos')

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_permiso'
        unique_together = ('idUser', 'idGroup', 'idPropiedad')
        indexes = [
            models.Index(fields=['idUser', 'idGroup', 'idPropiedad']),
        ]

    def __str__(self):
        return f"Permiso de usuario {self.idUser.username} en grupo {self.idGroup.name} para propiedad {self.idPropiedad.descripcion}"

class Propiedad(models.Model):
    descripcion = models.CharField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        self.descripcion = self.descripcion.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.descripcion

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_propiedad'

class PermisoValor(models.Model):
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, related_name='valores')
    valor = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        self.valor = self.valor.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.valor} (Para permiso ID {self.permiso.id})"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_permisovalor'


class Auditoria(models.Model):
    class Accion(models.TextChoices):
        LOGIN = 'LOGIN', 'Inicio de Sesión'
        LOGOUT = 'LOGOUT', 'Cierre de Sesión'
        CARGA_MANIFIESTO = 'CARGA_MANIFIESTO', 'Carga de un manifiesto'
        RECIBIR_MANIFIESTO = 'RECIBIR_MANIFIESTO', 'Recibir envios de un manifiesto' 
        RECIBIR_ENTRADA = 'RECIBIR_ENTRADA', 'Recibir Entrada'
        CREAR_ENVIO = 'CREAR_ENVIO', 'Crear Envío'
        EDITAR_ENVIO = 'EDITAR_ENVIO', 'Editar Envío'
        DESPACHO = 'DESPACHO', 'Despacho a mensajero'
        RECIBIR_TRANSFERENCIA = 'RECIBIR_TRANSFERENCIA', 'Recibir Transferencia'
        ELIMINAR_ENVIO = 'ELIMINAR_ENVIO', 'Eliminar Envío'
        CREAR_TRANSFERENCIA = 'CREAR_TRANSFERENCIA', 'Crear Transferencia'
        EDITAR_TRANSFERENCIA = 'EDITAR_TRANSFERENCIA', 'Editar Transferencia'
        ELIMINAR_TRANSFERENCIA = 'ELIMINAR_TRANSFERENCIA', 'Eliminar Transferencia'
        CAMBIO_ESTADO_ENVIO = 'CAMBIO_ESTADO_ENVIO', 'Cambio de Estado de Envío'

        # Agrega aquí más acciones según tus necesidades

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    accion = models.CharField(max_length=50, choices=Accion.choices)
    #descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.fecha} - {self.usuario} - {self.get_accion_display()}"

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_auditoria'
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        ordering = ['-fecha']

class TarifaImpuesto(models.Model):
    locacion = models.ForeignKey(
        'Locacion',
        on_delete=models.CASCADE,
        related_name='tarifas',
        verbose_name='Almacén'
    )
    peso_minimo_lb = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Peso mínimo (lb)'
    )
    peso_maximo_lb = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Peso máximo (lb)'
    )
    precio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Precio'
    )

    class Meta:
        managed = False
        db_table = 'hmpaquetesapp_tarifaimpuesto'
        verbose_name = 'Tarifa de Impuesto'
        verbose_name_plural = 'Tarifas de Impuestos'
        unique_together = ('locacion', 'peso_minimo_lb', 'peso_maximo_lb')
        ordering = ['locacion', 'peso_minimo_lb']

    def __str__(self):
        return f"Tarifa para {self.locacion.nombre}: {self.peso_minimo_lb}lb - {self.peso_maximo_lb}lb"