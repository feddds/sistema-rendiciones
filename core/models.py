from django.db import models

class Chofer(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    celular = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    vencimiento_licencia = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.nombre
        
        
class Vehiculo(models.Model):
    alias = models.CharField(max_length=50, blank=True)
    patente = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año = models.PositiveIntegerField(null=True, blank=True)
    numero_chasis = models.CharField(max_length=100, blank=True)
    numero_motor = models.CharField(max_length=100, blank=True)
    seguro_vencimiento = models.DateField(null=True, blank=True)
    seguro_empresa = models.CharField(max_length=100, blank=True)
    vtv_vencimiento = models.DateField(null=True, blank=True)
    kilometraje = models.PositiveIntegerField(null=True, blank=True)
    titular_uber = models.ForeignKey(Chofer, related_name='vehiculos_uber', null=True, blank=True, on_delete=models.SET_NULL)
    titular_cabify = models.ForeignKey(Chofer, related_name='vehiculos_cabify', null=True, blank=True, on_delete=models.SET_NULL)
    activo = models.BooleanField(default=True)

    def __str__(self):
        nombre = f"{self.alias} - " if self.alias else ""
        return f"{nombre}{self.marca} {self.modelo} ({self.patente})"


class Rendicion(models.Model):
    chofer = models.ForeignKey(Chofer, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_cierre = models.DateField(null=True, blank=True)
    cerrada = models.BooleanField(default=False)

    @property
    def total_ingresos(self):
        return sum(viaje.ingresos for viaje in self.viajes.all())

    @property
    def total_egresos(self):
        return sum(viaje.egresos for viaje in self.viajes.all())

    @property
    def total_neto(self):
        return self.total_ingresos - self.total_egresos

    def __str__(self):
        return f"Rendición #{self.id} de {self.chofer} - {self.fecha_creacion}"
        

    def __str__(self):
        return f"Rendición de {self.chofer} - {self.fecha_creacion}"


class Viaje(models.Model):
    TIPO_CHOICES = [
        ('UBER', 'Uber'),
        ('CABIFY', 'Cabify'),
        ('EXTRA', 'Extra'),
    ]

    rendicion = models.ForeignKey(Rendicion, on_delete=models.CASCADE, related_name='viajes')
    tipo_servicio = models.CharField(max_length=10, choices=TIPO_CHOICES)
    ingresos = models.DecimalField(max_digits=10, decimal_places=2)
    egresos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    beneficiario_real = models.ForeignKey(Chofer, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        chofer = self.rendicion.chofer
        vehiculo = self.rendicion.vehiculo

        if self.tipo_servicio == 'UBER':
            self.beneficiario_real = chofer if vehiculo.titular_uber == chofer else vehiculo.titular_uber
        elif self.tipo_servicio == 'CABIFY':
            self.beneficiario_real = chofer if vehiculo.titular_cabify == chofer else vehiculo.titular_cabify
        else:  # EXTRA u otro
            self.beneficiario_real = chofer

        super().save(*args, **kwargs)

