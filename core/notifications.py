"""
Sistema de notificaciones para el SaaS.
Por ahora simula el envío, pero está preparado para integración con Twilio.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from .models import Appointment

logger = logging.getLogger(__name__)


def send_whatsapp_reminder(appointment_id):
    """
    Envía un recordatorio por WhatsApp 15 minutos antes de la cita.
    
    Args:
        appointment_id: ID de la cita (Appointment)
    
    Returns:
        bool: True si se programó exitosamente, False en caso contrario
    """
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Validar que la cita no sea un bloqueo
        if appointment.is_block:
            logger.info(f"Cita {appointment_id} es un bloqueo, no se envía recordatorio")
            return False
        
        # Validar que la cita tenga cliente
        if not appointment.client:
            logger.warning(f"Cita {appointment_id} no tiene cliente asociado")
            return False
        
        # Calcular tiempo hasta la cita
        time_until_appointment = appointment.start_time - timezone.now()
        
        if time_until_appointment.total_seconds() < 0:
            logger.info(f"Cita {appointment_id} ya pasó, no se envía recordatorio")
            return False
        
        # Preparar mensaje
        client_name = appointment.client.get_full_name() or appointment.client.email
        business_name = appointment.business.name
        service_name = appointment.service.name
        appointment_time = appointment.start_time.strftime('%d/%m/%Y a las %H:%M')
        
        message = (
            f"🔔 Recordatorio: Tienes una cita en {business_name}\n\n"
            f"📅 Fecha: {appointment_time}\n"
            f"💇 Servicio: {service_name}\n"
            f"⏱️ Duración: {appointment.service.duration_minutes} minutos\n\n"
            f"¡Te esperamos!"
        )
        
        # Por ahora, simular el envío
        # TODO: Integrar con Twilio API
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=message,
        #     from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
        #     to=f'whatsapp:{appointment.client.phone}'
        # )
        
        # Simulación: imprimir en consola
        phone = appointment.client.phone or "N/A"
        print(f"\n{'='*60}")
        print(f"📱 WHATSAPP REMINDER SIMULADO")
        print(f"{'='*60}")
        print(f"Para: {phone}")
        print(f"Cliente: {client_name}")
        print(f"Mensaje:\n{message}")
        print(f"{'='*60}\n")
        
        logger.info(f"Recordatorio WhatsApp simulado para cita {appointment_id} - Cliente: {client_name}")
        
        return True
        
    except Appointment.DoesNotExist:
        logger.error(f"Cita {appointment_id} no encontrada")
        return False
    except Exception as e:
        logger.error(f"Error al enviar recordatorio WhatsApp para cita {appointment_id}: {str(e)}")
        return False


def schedule_whatsapp_reminder(appointment_id, minutes_before=15):
    """
    Programa un recordatorio de WhatsApp para X minutos antes de la cita.
    
    Args:
        appointment_id: ID de la cita
        minutes_before: Minutos antes de la cita para enviar el recordatorio (default: 15)
    
    Returns:
        bool: True si se programó exitosamente
    """
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Calcular cuándo enviar el recordatorio
        reminder_time = appointment.start_time - timedelta(minutes=minutes_before)
        current_time = timezone.now()
        
        if reminder_time <= current_time:
            # Si el tiempo ya pasó, enviar inmediatamente
            logger.info(f"Tiempo de recordatorio ya pasó para cita {appointment_id}, enviando inmediatamente")
            return send_whatsapp_reminder(appointment_id)
        
        # Por ahora, solo imprimir en consola
        # TODO: Integrar con Celery o similar para programar tareas
        # from celery import shared_task
        # send_whatsapp_reminder.apply_async(
        #     args=[appointment_id],
        #     eta=reminder_time
        # )
        
        time_until_reminder = reminder_time - current_time
        hours = int(time_until_reminder.total_seconds() // 3600)
        minutes = int((time_until_reminder.total_seconds() % 3600) // 60)
        
        print(f"\n{'='*60}")
        print(f"⏰ PROGRAMANDO RECORDATORIO")
        print(f"{'='*60}")
        print(f"Cita ID: {appointment_id}")
        print(f"Hora de la cita: {appointment.start_time.strftime('%d/%m/%Y %H:%M')}")
        print(f"Recordatorio programado: {minutes_before} min antes")
        print(f"Se enviará en: {hours}h {minutes}m")
        print(f"{'='*60}\n")
        
        logger.info(
            f"Recordatorio programado para cita {appointment_id} - "
            f"Se enviará {minutes_before} min antes de {appointment.start_time}"
        )
        
        return True
        
    except Appointment.DoesNotExist:
        logger.error(f"Cita {appointment_id} no encontrada para programar recordatorio")
        return False
    except Exception as e:
        logger.error(f"Error al programar recordatorio para cita {appointment_id}: {str(e)}")
        return False
