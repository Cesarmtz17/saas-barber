"""
Señales de Django para el modelo Appointment.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment
from .notifications import schedule_whatsapp_reminder


@receiver(post_save, sender=Appointment)
def appointment_created_handler(sender, instance, created, **kwargs):
    """
    Señal que se dispara cuando se crea una nueva cita.
    Programa un recordatorio de WhatsApp 15 minutos antes.
    """
    if created and not instance.is_block:
        # Solo programar recordatorios para citas reales (no bloqueos)
        if instance.client and instance.service:
            schedule_whatsapp_reminder(instance.id, minutes_before=15)
