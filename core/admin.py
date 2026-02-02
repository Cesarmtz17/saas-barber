from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django import forms
from .models import CustomUser, Business, Service, Appointment, GalleryImage


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Admin personalizado para CustomUser."""
    list_display = ['email', 'first_name', 'last_name', 'phone', 'is_owner', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_owner', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permisos', {'fields': ('is_owner', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_owner', 'is_staff', 'is_superuser'),
        }),
    )


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    """Admin para Business."""
    list_display = ['name', 'slug', 'owner', 'timezone', 'capacity', 'is_active', 'created_at']
    list_filter = ['is_active', 'timezone', 'created_at']
    search_fields = ['name', 'slug', 'owner__email']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'schedule_display']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('owner', 'name', 'slug', 'is_active', 'timezone', 'capacity')
        }),
        ('Contacto', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Personalización de Landing Page', {
            'fields': ('description', 'logo_url', 'hero_image_url', 'primary_color'),
            'description': format_html(
                '<p><strong>Personaliza la apariencia de tu página web.</strong></p>'
                '<p>• <strong>Descripción:</strong> Texto que aparecerá en la landing page</p>'
                '<p>• <strong>Logo URL:</strong> URL de tu logo (puedes usar servicios como Imgur, Cloudinary, etc.)</p>'
                '<p>• <strong>Hero Image URL:</strong> URL de la imagen principal (recomendado: 1920x1080px)</p>'
                '<p>• <strong>Color Principal:</strong> Color de marca en formato hexadecimal (ej: #000000 para negro, #FF6B35 para naranja)</p>'
            )
        }),
        ('Redes Sociales', {
            'fields': ('instagram_url', 'facebook_url')
        }),
        ('Galería', {
            'fields': ('gallery_json',),
            'description': format_html(
                '<p><strong>Galería de imágenes de trabajos realizados.</strong></p>'
                '<p>Formato JSON array (copia y pega este ejemplo):</p>'
                '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 12px;">'
                '[\n'
                '  "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&q=80",\n'
                '  "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?auto=format&fit=crop&q=80"\n'
                ']'
                '</pre>'
            )
        }),
        ('Horarios', {
            'fields': ('schedule_config', 'schedule_display'),
            'description': format_html(
                '<p><strong>Configura los horarios de atención por día de la semana.</strong></p>'
                '<p>Formato JSON (copia y pega este ejemplo y modifica según necesites):</p>'
                '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 12px;">'
                '{{\n'
                '  "monday": {{"open": "09:00", "close": "20:00", "enabled": true}},\n'
                '  "tuesday": {{"open": "09:00", "close": "20:00", "enabled": true}},\n'
                '  "wednesday": {{"open": "09:00", "close": "20:00", "enabled": true}},\n'
                '  "thursday": {{"open": "09:00", "close": "20:00", "enabled": true}},\n'
                '  "friday": {{"open": "09:00", "close": "20:00", "enabled": true}},\n'
                '  "saturday": {{"open": "09:00", "close": "20:00", "enabled": true}},\n'
                '  "sunday": {{"open": "09:00", "close": "20:00", "enabled": false}}\n'
                '}}'
                '</pre>'
            )
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def schedule_display(self, obj):
        """Muestra la configuración de horarios de forma legible."""
        if not obj.schedule_config:
            return "Sin configuración"
        
        days = {
            'monday': 'Lunes',
            'tuesday': 'Martes',
            'wednesday': 'Miércoles',
            'thursday': 'Jueves',
            'friday': 'Viernes',
            'saturday': 'Sábado',
            'sunday': 'Domingo',
        }
        
        html = "<ul style='list-style: none; padding: 0;'>"
        for day_key, day_name in days.items():
            day_config = obj.schedule_config.get(day_key, {})
            if day_config.get('enabled', False):
                html += f"<li><strong>{day_name}:</strong> {day_config.get('open', 'N/A')} - {day_config.get('close', 'N/A')}</li>"
            else:
                html += f"<li><strong>{day_name}:</strong> <span style='color: #999;'>Cerrado</span></li>"
        html += "</ul>"
        return format_html(html)
    
    schedule_display.short_description = 'Vista Previa de Horarios'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin para Service."""
    list_display = ['name', 'business', 'duration_minutes', 'price', 'is_active', 'created_at']
    list_filter = ['is_active', 'business', 'created_at']
    search_fields = ['name', 'business__name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('business', 'name', 'description', 'is_active')
        }),
        ('Detalles del Servicio', {
            'fields': ('duration_minutes', 'price')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    """Admin para GalleryImage."""
    list_display = ['business', 'image', 'caption', 'order', 'created_at']
    list_filter = ['business', 'created_at']
    search_fields = ['business__name', 'caption']
    ordering = ['business', 'order', '-created_at']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin para Appointment."""
    list_display = ['__str__', 'business', 'client', 'service', 'start_time', 'end_time', 'status', 'is_block', 'created_at']
    list_filter = ['status', 'is_block', 'business', 'start_time', 'created_at']
    search_fields = ['business__name', 'client__email', 'service__name', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Información de la Cita', {
            'fields': ('business', 'client', 'service', 'status', 'is_block')
        }),
        ('Horarios', {
            'fields': ('start_time', 'end_time')
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
