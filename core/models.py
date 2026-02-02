from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.utils.text import slugify
import json


class CustomUserManager(BaseUserManager):
    """Manager personalizado para CustomUser con email como username."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Crea y retorna un usuario con email y password."""
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y retorna un superusuario."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_owner', False)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado que usa email como username.
    """
    email = models.EmailField('Email', unique=True, db_index=True)
    phone = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    first_name = models.CharField('Nombre', max_length=150, blank=True)
    last_name = models.CharField('Apellido', max_length=150, blank=True)
    is_owner = models.BooleanField('Es Propietario', default=False, help_text='Indica si el usuario es propietario de un negocio')
    
    # Campos requeridos por Django
    is_staff = models.BooleanField('Es Staff', default=False)
    is_active = models.BooleanField('Activo', default=True)
    date_joined = models.DateTimeField('Fecha de Registro', default=timezone.now)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def get_short_name(self):
        """Retorna el nombre corto del usuario."""
        return self.first_name or self.email


class Business(models.Model):
    """
    Modelo de negocio (entidad multitenant principal).
    Cada negocio pertenece a un propietario y tiene servicios y citas.
    """
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='businesses',
        verbose_name='Propietario',
        limit_choices_to={'is_owner': True}
    )
    name = models.CharField('Nombre del Negocio', max_length=200)
    slug = models.SlugField('Slug', unique=True, max_length=200, db_index=True)
    address = models.TextField('Dirección', blank=True, null=True)
    phone = models.CharField('Teléfono del Negocio', max_length=20, blank=True, null=True)
    email = models.EmailField('Email del Negocio', blank=True, null=True)
    
    # Configuración de horarios en formato JSON
    # Ejemplo: {"monday": {"open": "09:00", "close": "18:00", "enabled": true}, ...}
    schedule_config = models.JSONField(
        'Configuración de Horarios',
        default=dict,
        help_text='Configuración de horarios de atención por día de la semana'
    )
    
    # Zona horaria del negocio (por defecto la del sistema)
    timezone = models.CharField(
        'Zona Horaria',
        max_length=50,
        default='America/Monterrey',
        help_text='Zona horaria del negocio (ej: America/Monterrey, America/Mexico_City)'
    )
    
    # Capacidad del negocio (número de barberos/estaciones disponibles)
    capacity = models.PositiveIntegerField(
        'Capacidad',
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Número de barberos o estaciones disponibles simultáneamente'
    )
    
    # Campos de personalización de la landing page
    description = models.TextField(
        'Descripción del Negocio',
        blank=True,
        null=True,
        help_text='Breve historia o descripción del negocio para la landing page'
    )
    hero_image_url = models.URLField(
        'URL de Imagen Hero',
        blank=True,
        null=True,
        help_text='URL de la imagen principal para la sección hero'
    )
    logo_url = models.URLField(
        'URL del Logo',
        blank=True,
        null=True,
        help_text='URL del logo del negocio'
    )
    primary_color = models.CharField(
        'Color Principal',
        max_length=7,
        default='#000000',
        help_text='Color de marca en formato hexadecimal (ej: #000000)'
    )
    instagram_url = models.URLField(
        'URL de Instagram',
        blank=True,
        null=True,
        help_text='URL del perfil de Instagram'
    )
    facebook_url = models.URLField(
        'URL de Facebook',
        blank=True,
        null=True,
        help_text='URL del perfil de Facebook'
    )
    gallery_json = models.JSONField(
        'Galería de Imágenes',
        default=list,
        blank=True,
        help_text='Lista de URLs de imágenes de trabajos realizados (formato JSON array)'
    )
    
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Negocio'
        verbose_name_plural = 'Negocios'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Genera el slug automáticamente si no existe."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_default_schedule(self):
        """Retorna la configuración de horarios por defecto."""
        return {
            "monday": {"open": "09:00", "close": "20:00", "enabled": True},
            "tuesday": {"open": "09:00", "close": "20:00", "enabled": True},
            "wednesday": {"open": "09:00", "close": "20:00", "enabled": True},
            "thursday": {"open": "09:00", "close": "20:00", "enabled": True},
            "friday": {"open": "09:00", "close": "20:00", "enabled": True},
            "saturday": {"open": "09:00", "close": "20:00", "enabled": True},
            "sunday": {"open": "09:00", "close": "20:00", "enabled": False},
        }
    
    def get_local_now(self):
        """Retorna la fecha/hora actual en la zona horaria del negocio."""
        from django.utils import timezone as tz
        from zoneinfo import ZoneInfo
        
        try:
            business_tz = ZoneInfo(self.timezone)
            return tz.now().astimezone(business_tz)
        except Exception:
            # Si hay error con la zona horaria, usar la del sistema
            return tz.now()
    
    def get_local_today(self):
        """Retorna la fecha de hoy en la zona horaria del negocio."""
        return self.get_local_now().date()


class Service(models.Model):
    """
    Modelo de servicio ofrecido por un negocio.
    Cada servicio pertenece a un Business (multitenant).
    """
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='Negocio'
    )
    name = models.CharField('Nombre del Servicio', max_length=200)
    description = models.TextField('Descripción', blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(
        'Duración (minutos)',
        validators=[MinValueValidator(1)],
        help_text='Duración del servicio en minutos'
    )
    price = models.DecimalField(
        'Precio',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Precio del servicio'
    )
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['name']
        unique_together = [['business', 'name']]
    
    def __str__(self):
        return f"{self.business.name} - {self.name}"


class Appointment(models.Model):
    """
    Modelo de cita/reserva.
    Cada cita pertenece a un Business (multitenant), tiene un cliente y un servicio.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'No se presentó'),
        ('completed', 'Completada'),
    ]
    
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Negocio'
    )
    client = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Cliente'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Servicio',
        null=True,
        blank=True,
        help_text='Opcional para bloqueos'
    )
    start_time = models.DateTimeField('Hora de Inicio', db_index=True)
    end_time = models.DateTimeField('Hora de Fin', db_index=True)
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    notes = models.TextField('Notas', blank=True, null=True, help_text='Notas adicionales sobre la cita')
    is_block = models.BooleanField(
        'Es Bloqueo',
        default=False,
        help_text='Si está marcado, este horario está bloqueado y no disponible para clientes'
    )
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['business', 'start_time']),
            models.Index(fields=['client', 'start_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        if self.is_block:
            return f"{self.business.name} - BLOQUEO - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
        return f"{self.business.name} - {self.client.email} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """Valida que end_time sea posterior a start_time y que las citas tengan servicio."""
        from django.core.exceptions import ValidationError
        # Solo validar end_time si ya está definido
        if self.end_time and self.end_time <= self.start_time:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        if not self.is_block and not self.service:
            raise ValidationError('Las citas deben tener un servicio asignado.')
    
    def save(self, *args, **kwargs):
        """Valida y calcula end_time si no está definido."""
        # Calcular end_time ANTES de validar
        if not self.end_time:
            from datetime import timedelta
            if self.service:
                self.end_time = self.start_time + timedelta(minutes=self.service.duration_minutes)
            elif self.is_block:
                # Bloqueos sin servicio duran 1 hora por defecto
                self.end_time = self.start_time + timedelta(hours=1)
        
        # Ahora validar con end_time ya calculado
        self.full_clean()
        super().save(*args, **kwargs)


class GalleryImage(models.Model):
    """
    Modelo para almacenar imágenes de la galería de trabajos de un negocio.
    """
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='gallery_images',
        verbose_name='Negocio'
    )
    image = models.ImageField(
        'Imagen',
        upload_to='gallery/%Y/%m/%d/',
        help_text='Imagen de trabajo realizado'
    )
    caption = models.CharField(
        'Descripción',
        max_length=200,
        blank=True,
        null=True,
        help_text='Descripción opcional de la imagen'
    )
    order = models.IntegerField(
        'Orden',
        default=0,
        help_text='Orden de visualización (menor número aparece primero)'
    )
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Imagen de Galería'
        verbose_name_plural = 'Imágenes de Galería'
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.business.name} - {self.image.name}"
