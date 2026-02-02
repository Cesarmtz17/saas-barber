"""
Service layer para lógica de negocio relacionada con citas y disponibilidad.
"""
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db.models import Q
from .models import Business, Service, Appointment


class AvailabilityService:
    """
    Servicio para calcular slots disponibles para citas.
    """
    
    @staticmethod
    def get_available_slots(business, service, date):
        """
        Calcula los slots disponibles para un servicio en una fecha específica.
        
        Args:
            business: Instancia de Business
            service: Instancia de Service
            date: datetime.date - Fecha para la cual calcular slots
        
        Returns:
            list: Lista de datetime.datetime con los slots disponibles
        """
        # Obtener configuración de horarios del negocio
        schedule_config = business.schedule_config or business.get_default_schedule()
        
        # Obtener el día de la semana (0=lunes, 6=domingo)
        weekday = date.weekday()
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_key = day_names[weekday]
        
        # Verificar si el día está habilitado
        day_config = schedule_config.get(day_key, {})
        if not day_config.get('enabled', False):
            return []
        
        # Obtener horarios de apertura y cierre
        open_time_str = day_config.get('open', '09:00')
        close_time_str = day_config.get('close', '18:00')
        
        # Parsear horarios
        open_hour, open_minute = map(int, open_time_str.split(':'))
        close_hour, close_minute = map(int, close_time_str.split(':'))
        
        open_time = time(open_hour, open_minute)
        close_time = time(close_hour, close_minute)
        
        # Obtener la zona horaria del negocio
        from zoneinfo import ZoneInfo
        try:
            business_tz = ZoneInfo(business.timezone)
        except Exception:
            business_tz = timezone.get_current_timezone()
        
        # Crear datetime para inicio y fin del día en la zona horaria del negocio
        start_datetime_naive = datetime.combine(date, open_time)
        end_datetime_naive = datetime.combine(date, close_time)
        
        # Asignar zona horaria del negocio
        start_datetime = start_datetime_naive.replace(tzinfo=business_tz)
        end_datetime = end_datetime_naive.replace(tzinfo=business_tz)
        
        # Obtener la hora actual en la zona horaria del negocio
        now_in_business_tz = timezone.now().astimezone(business_tz)
        today_in_business_tz = now_in_business_tz.date()
        
        # Obtener citas existentes y bloqueos para ese día y negocio
        # Optimización: usar select_related y solo campos necesarios
        existing_appointments = Appointment.objects.filter(
            business=business,
            start_time__date=date
        ).filter(
            Q(status__in=['pending', 'confirmed']) | Q(is_block=True)
        ).only('start_time', 'end_time', 'is_block').order_by('start_time')
        
        # Generar todos los posibles slots (cada 15 minutos)
        slot_duration = timedelta(minutes=15)
        service_duration = timedelta(minutes=service.duration_minutes)
        
        # Obtener capacidad del negocio
        capacity = business.capacity or 1
        
        available_slots = []
        current_slot = start_datetime
        
        while current_slot + service_duration <= end_datetime:
            slot_end = current_slot + service_duration
            
            # Verificar capacidad: contar citas simultáneas en el intervalo del slot
            is_available = AvailabilityService._check_slot_capacity(
                current_slot, slot_end, existing_appointments, capacity
            )
            
            # Verificar que no sea en el pasado
            # Si es el día de hoy, solo mostrar horas futuras (verificar que el slot completo termine en el futuro)
            if date == today_in_business_tz:
                # Para hoy, verificar que el slot completo (incluyendo duración) esté en el futuro
                # slot_end ya está en la zona horaria del negocio porque current_slot la tiene
                if is_available and slot_end > now_in_business_tz:
                    available_slots.append(current_slot)
            else:
                # Para días futuros, verificar que el inicio del slot esté en el futuro
                if is_available and current_slot > now_in_business_tz:
                    available_slots.append(current_slot)
            
            current_slot += slot_duration
        
        return available_slots
    
    @staticmethod
    def _check_slot_capacity(slot_start, slot_end, existing_appointments, capacity):
        """
        Verifica si un slot tiene capacidad disponible considerando citas simultáneas.
        
        Args:
            slot_start: datetime.datetime - Inicio del slot
            slot_end: datetime.datetime - Fin del slot
            existing_appointments: QuerySet de Appointment - Citas existentes del día
            capacity: int - Capacidad máxima del negocio
        
        Returns:
            bool: True si hay capacidad disponible, False en caso contrario
        """
        # Filtrar solo las citas que se solapan con el slot
        overlapping_appointments = [
            apt for apt in existing_appointments
            if not (slot_end <= apt.start_time or slot_start >= apt.end_time)
        ]
        
        if not overlapping_appointments:
            return True
        
        # Si hay más citas solapadas que la capacidad, el slot no está disponible
        if len(overlapping_appointments) >= capacity:
            return False
        
        # Verificar capacidad usando algoritmo de eventos (sweep line)
        # Creamos eventos de inicio y fin de citas dentro del rango del slot
        events = []
        for apt in overlapping_appointments:
            # Evento de inicio: cuando la cita empieza (o inicio del slot si empieza antes)
            start_event_time = max(apt.start_time, slot_start)
            events.append((start_event_time, 1))  # +1 para inicio
            
            # Evento de fin: cuando la cita termina (o fin del slot si termina después)
            end_event_time = min(apt.end_time, slot_end)
            events.append((end_event_time, -1))  # -1 para fin
        
        # Ordenar eventos por tiempo (si hay empate, procesar fin antes que inicio)
        events.sort(key=lambda x: (x[0], x[1]))
        
        # Contar máximo de citas simultáneas recorriendo los eventos
        concurrent_count = 0
        max_concurrent = 0
        
        for event_time, delta in events:
            concurrent_count += delta
            max_concurrent = max(max_concurrent, concurrent_count)
            
            # Si en algún momento alcanzamos la capacidad, el slot no está disponible
            if max_concurrent >= capacity:
                return False
        
        return True
    
    @staticmethod
    def is_slot_available(business, service, start_time):
        """
        Verifica si un slot específico está disponible.
        
        Args:
            business: Instancia de Business
            service: Instancia de Service
            start_time: datetime.datetime - Hora de inicio a verificar
        
        Returns:
            bool: True si el slot está disponible, False en caso contrario
        """
        end_time = start_time + timedelta(minutes=service.duration_minutes)
        
        # Obtener capacidad del negocio
        capacity = business.capacity or 1
        
        # Obtener citas que se solapan con el slot
        overlapping_appointments = Appointment.objects.filter(
            business=business,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).filter(
            Q(status__in=['pending', 'confirmed']) | Q(is_block=True)
        ).only('start_time', 'end_time', 'is_block')
        
        # Verificar capacidad usando el mismo algoritmo
        if not AvailabilityService._check_slot_capacity(
            start_time, end_time, list(overlapping_appointments), capacity
        ):
            return False
        
        # Verificar que esté dentro del horario de atención
        schedule_config = business.schedule_config or business.get_default_schedule()
        weekday = start_time.weekday()
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_key = day_names[weekday]
        
        day_config = schedule_config.get(day_key, {})
        if not day_config.get('enabled', False):
            return False
        
        open_time_str = day_config.get('open', '09:00')
        close_time_str = day_config.get('close', '18:00')
        
        open_hour, open_minute = map(int, open_time_str.split(':'))
        close_hour, close_minute = map(int, close_time_str.split(':'))
        
        slot_time = start_time.time()
        open_time = time(open_hour, open_minute)
        close_time = time(close_hour, close_minute)
        
        if slot_time < open_time or slot_time >= close_time:
            return False
        
        # Obtener la zona horaria del negocio
        from zoneinfo import ZoneInfo
        try:
            business_tz = ZoneInfo(business.timezone)
        except Exception:
            business_tz = timezone.get_current_timezone()
        
        # Verificar que no sea en el pasado (en la zona horaria del negocio)
        now_in_business_tz = timezone.now().astimezone(business_tz)
        if start_time <= now_in_business_tz:
            return False
        
        return True
