from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta, date
from .models import Business, Service, Appointment, CustomUser, GalleryImage
from .services import AvailabilityService


def login_redirect_view(request):
    """
    Vista de redirección después del login.
    Redirige a los owners a su dashboard y a otros usuarios al admin.
    """
    if request.user.is_authenticated:
        if request.user.is_owner:
            # Intentar obtener el negocio del usuario
            try:
                business = Business.objects.get(owner=request.user, is_active=True)
                return redirect('core:dashboard', business_slug=business.slug)
            except Business.DoesNotExist:
                pass
            except Business.MultipleObjectsReturned:
                business = Business.objects.filter(owner=request.user, is_active=True).first()
                if business:
                    return redirect('core:dashboard', business_slug=business.slug)
        
        # Si no es owner o no tiene negocio, ir al admin
        return redirect('admin:index')
    
    # Si no está autenticado, ir al login
    return redirect('admin:login')


@login_required
def my_appointments_view(request):
    """
    Vista para que los clientes vean sus propias reservas.
    """
    # Obtener todas las citas del usuario actual
    appointments = Appointment.objects.filter(
        client=request.user,
        is_block=False  # Excluir bloqueos
    ).select_related('business', 'service').order_by('-start_time')
    
    # Separar por estado
    upcoming = appointments.filter(start_time__gte=timezone.now(), status__in=['pending', 'confirmed'])
    past = appointments.exclude(start_time__gte=timezone.now())
    
    context = {
        'upcoming_appointments': upcoming,
        'past_appointments': past,
        'total_appointments': appointments.count()
    }
    
    return render(request, 'core/my_appointments.html', context)


def home_view(request):
    """
    Página de inicio del SaaS (landing page).
    Ya no muestra listado de negocios, cada negocio tiene su propia URL.
    """
    return render(request, 'core/home.html', {})


def client_booking_view(request, business_slug):
    """
    Vista pública para que los clientes reserven citas.
    Muestra los servicios disponibles y permite seleccionar fecha/hora.
    """
    try:
        business = get_object_or_404(Business, slug=business_slug, is_active=True)
    except Exception as e:
        messages.error(request, f'Error al cargar el negocio: {str(e)}')
        return redirect('core:home')
    
    services = Service.objects.filter(business=business, is_active=True)
    
    # Obtener imágenes subidas de la galería
    gallery_images = GalleryImage.objects.filter(business=business).order_by('order', '-created_at')
    
    selected_service_id = request.GET.get('service')
    selected_date = request.GET.get('date')
    
    selected_service = None
    available_slots = []
    
    # Generar opciones de fechas (próximos 14 días) en la zona horaria del negocio
    date_options = []
    today = business.get_local_today()
    day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    
    for i in range(14):
        future_date = today + timedelta(days=i)
        weekday = future_date.weekday()
        date_options.append({
            'date': future_date,
            'day_name': day_names[weekday]
        })
    
    if selected_service_id:
        try:
            selected_service = Service.objects.get(id=selected_service_id, business=business, is_active=True)
        except Service.DoesNotExist:
            messages.error(request, 'Servicio no encontrado.')
    
    if selected_service and selected_date:
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            available_slots = AvailabilityService.get_available_slots(business, selected_service, date_obj)
        except ValueError:
            messages.error(request, 'Fecha inválida.')
    
    context = {
        'business': business,
        'services': services,
        'selected_service': selected_service,
        'selected_date': selected_date,
        'available_slots': available_slots,
        'date_options': date_options,
        'gallery_images': gallery_images,
    }
    
    return render(request, 'core/client_booking.html', context)


@login_required
def dashboard_view(request, business_slug=None):
    """
    Dashboard para BusinessOwner.
    Muestra las citas del día seleccionado o de la semana.
    """
    # Si no se proporciona business_slug, obtener el negocio del usuario y redirigir
    if not business_slug:
        # Verificar si el usuario es propietario
        if not request.user.is_owner:
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('admin:index')
        
        # Obtener el negocio del usuario
        try:
            business = Business.objects.get(owner=request.user, is_active=True)
            # Redirigir al dashboard con el slug del negocio
            return redirect('core:dashboard', business_slug=business.slug)
        except Business.DoesNotExist:
            messages.warning(request, 'No tienes un negocio registrado. Contacta al administrador.')
            return redirect('admin:index')
        except Business.MultipleObjectsReturned:
            business = Business.objects.filter(owner=request.user, is_active=True).first()
            return redirect('core:dashboard', business_slug=business.slug)
    else:
        # Si se proporciona business_slug, verificar que el usuario sea el dueño
        business = get_object_or_404(Business, slug=business_slug, is_active=True)
        if business.owner != request.user:
            messages.error(request, 'No tienes permiso para acceder a este dashboard.')
            return redirect('admin:index')
    
    # Obtener fecha seleccionada (por defecto hoy en la zona horaria del negocio)
    selected_date_str = request.GET.get('date')
    business_today = business.get_local_today()
    
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = business_today
    else:
        selected_date = business_today
    
    # Generar opciones de fechas (hoy y próximos 6 días = 7 días en total)
    date_options = []
    today = business_today
    day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    
    for i in range(7):
        future_date = today + timedelta(days=i)
        weekday = future_date.weekday()
        date_options.append({
            'date': future_date,
            'day_name': day_names[weekday],
            'is_today': future_date == today,
            'is_selected': future_date == selected_date
        })
    
    # Obtener citas del día seleccionado
    appointments = Appointment.objects.filter(
        business=business,
        start_time__date=selected_date
    ).select_related('client', 'service').order_by('start_time')
    
    # Generar todas las horas del día para el calendario
    schedule_config = business.schedule_config or business.get_default_schedule()
    weekday = selected_date.weekday()
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_key = day_names[weekday]
    day_config = schedule_config.get(day_key, {})
    
    # Horarios del día
    open_time_str = day_config.get('open', '09:00') if day_config.get('enabled', False) else '09:00'
    close_time_str = day_config.get('close', '20:00') if day_config.get('enabled', False) else '20:00'
    
    open_hour, open_minute = map(int, open_time_str.split(':'))
    close_hour, close_minute = map(int, close_time_str.split(':'))
    
    # Generar todas las horas del día (cada 15 minutos)
    time_slots = []
    current_hour = open_hour
    current_minute = open_minute
    
    while current_hour < close_hour or (current_hour == close_hour and current_minute < close_minute):
        time_str = f"{current_hour:02d}:{current_minute:02d}"
        time_slots.append({
            'time': time_str,
            'hour': current_hour,
            'minute': current_minute
        })
        
        current_minute += 15
        if current_minute >= 60:
            current_minute = 0
            current_hour += 1
    
    # Crear un diccionario de citas por hora para fácil acceso
    appointments_by_time = {}
    for apt in appointments:
        apt_time = apt.start_time.time()
        time_key = f"{apt_time.hour:02d}:{apt_time.minute:02d}"
        if time_key not in appointments_by_time:
            appointments_by_time[time_key] = apt
    
    # Crear lista de slots con su cita asociada
    # Solo mostrar la cita en el slot de inicio, no en los slots intermedios
    time_slots_with_appointments = []
    for slot in time_slots:
        appointment = appointments_by_time.get(slot['time'])
        time_slots_with_appointments.append({
            'time': slot['time'],
            'hour': slot['hour'],
            'minute': slot['minute'],
            'appointment': appointment
        })
    
    # Estadísticas del día seleccionado
    total = appointments.count()
    confirmed = appointments.filter(status='confirmed').count()
    pending = appointments.filter(status='pending').count()
    completed = appointments.filter(status='completed').count()
    
    context = {
        'business': business,
        'appointments': appointments,
        'selected_date': selected_date,
        'date_options': date_options,
        'time_slots': time_slots_with_appointments,
        'stats': {
            'total': total,
            'confirmed': confirmed,
            'pending': pending,
            'completed': completed,
        }
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def update_appointment_status(request, business_slug, appointment_id):
    """
    Actualiza el estado de una cita (confirmar, no-asistió, completar).
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    business = get_object_or_404(Business, slug=business_slug, is_active=True)
    
    # Verificar que el usuario sea el dueño del negocio
    if appointment.business != business or business.owner != request.user:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('core:dashboard', business_slug=business.slug)
    
    new_status = request.POST.get('status')
    valid_statuses = ['pending', 'confirmed', 'cancelled', 'no_show', 'completed']
    
    if new_status in valid_statuses:
        appointment.status = new_status
        appointment.save()
        messages.success(request, f'Cita {appointment.get_status_display().lower()}.')
    else:
        messages.error(request, 'Estado inválido.')
    
    # Redirigir con la fecha actual para mantener el contexto
    selected_date = request.POST.get('selected_date', timezone.now().date())
    return redirect(f"{reverse('core:dashboard', args=[business.slug])}?date={selected_date}")


@csrf_exempt
@require_http_methods(["POST"])
def create_appointment(request, business_slug):
    """
    Crea una nueva cita desde la página pública de reservas.
    """
    business = get_object_or_404(Business, slug=business_slug, is_active=True)
    
    try:
        service_id = request.POST.get('service_id')
        start_time_str = request.POST.get('start_time')
        notes = request.POST.get('notes', '')
        
        if not service_id or not start_time_str:
            return JsonResponse({'success': False, 'error': 'Datos incompletos. service_id o start_time faltantes.'})
        
        service = Service.objects.get(id=service_id, business=business, is_active=True)
        
        # Parsear el datetime (formato: YYYY-MM-DD HH:MM:SS)
        try:
            # Intentar formato con segundos
            dt = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            start_time = timezone.make_aware(dt)
        except ValueError:
            try:
                # Intentar formato sin segundos
                dt = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
                start_time = timezone.make_aware(dt)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Formato de fecha/hora inválido.'})
        
        # Verificar disponibilidad
        if not AvailabilityService.is_slot_available(business, service, start_time):
            return JsonResponse({'success': False, 'error': 'Este horario ya no está disponible.'})
        
        # Manejar autenticación/registro del cliente
        if request.user.is_authenticated:
            client = request.user
        else:
            # Crear o obtener usuario
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            phone = request.POST.get('phone', '')
            
            if not email or not password:
                return JsonResponse({'success': False, 'error': 'Email y contraseña son requeridos.'})
            
            # Intentar obtener usuario existente o crear uno nuevo
            try:
                client = CustomUser.objects.get(email=email)
                # Si el usuario existe, verificar contraseña
                if not client.check_password(password):
                    return JsonResponse({'success': False, 'error': 'Contraseña incorrecta.'})
            except CustomUser.DoesNotExist:
                # Crear nuevo usuario
                client = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    is_owner=False
                )
            
            # Autenticar al usuario
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
        
        # Crear la cita
        appointment = Appointment.objects.create(
            business=business,
            client=client,
            service=service,
            start_time=start_time,
            status='pending',
            notes=notes
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Reserva creada exitosamente.',
            'redirect_url': f'/{business.slug}/?success=1'
        })
        
    except Service.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Servicio no encontrado.'})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Error en los datos: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al crear la reserva: {str(e)}'})

@login_required
def block_time_view(request, business_slug=None):
    """
    Vista para que el BusinessOwner bloquee un horario.
    """
    # Si se proporciona business_slug, verificar que el usuario sea el dueño
    if business_slug:
        business = get_object_or_404(Business, slug=business_slug, is_active=True)
        if business.owner != request.user:
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('admin:index')
    else:
        if not request.user.is_owner:
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('admin:index')
        
        # Obtener el negocio del usuario
        try:
            business = Business.objects.get(owner=request.user, is_active=True)
        except Business.DoesNotExist:
            messages.warning(request, 'No tienes un negocio registrado.')
            return redirect('admin:index')
        except Business.MultipleObjectsReturned:
            business = Business.objects.filter(owner=request.user, is_active=True).first()
    
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date')
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            notes = request.POST.get('notes', '')
            
            if not date_str or not start_time_str:
                messages.error(request, 'Fecha y hora de inicio son requeridos.')
                return redirect('core:block_time', business_slug=business.slug)
            
            # Combinar fecha y hora
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_datetime = datetime.combine(date_obj, datetime.strptime(start_time_str, '%H:%M').time())
            start_time = timezone.make_aware(start_datetime)
            
            # Si no se proporciona end_time, usar 1 hora por defecto
            if end_time_str:
                end_datetime = datetime.combine(date_obj, datetime.strptime(end_time_str, '%H:%M').time())
                end_time = timezone.make_aware(end_datetime)
            else:
                end_time = start_time + timedelta(hours=1)
            
            # Verificar que no se solape con citas existentes
            overlapping = Appointment.objects.filter(
                business=business,
                start_time__lt=end_time,
                end_time__gt=start_time,
                is_block=False,
                status__in=['pending', 'confirmed']
            ).exists()
            
            if overlapping:
                messages.error(request, 'Este horario tiene citas confirmadas. No se puede bloquear.')
                return redirect('core:block_time', business_slug=business.slug)
            
            # Crear el bloqueo (los bloqueos no requieren cliente ni servicio)
            block_appointment = Appointment.objects.create(
                business=business,
                client=request.user,  # El dueño es el "cliente" del bloqueo (requerido por el modelo, pero no se usa)
                service=None,  # Los bloqueos no tienen servicio
                start_time=start_time,
                end_time=end_time,
                status='confirmed',  # Los bloqueos están confirmados por defecto
                is_block=True,
                notes=notes or 'Horario bloqueado por el propietario'
            )
            
            messages.success(request, f'Horario bloqueado exitosamente: {start_time.strftime("%d/%m/%Y %H:%M")} - {end_time.strftime("%H:%M")}')
            if business_slug:
                return redirect('core:dashboard', business_slug=business.slug)
            return redirect('core:dashboard')
            
        except ValueError as e:
            messages.error(request, f'Error en el formato de fecha/hora: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error al crear el bloqueo: {str(e)}')
    
    # Generar opciones de fechas (próximos 30 días) en la zona horaria del negocio
    date_options = []
    today = business.get_local_today()
    for i in range(30):
        future_date = today + timedelta(days=i)
        date_options.append(future_date)
    
    context = {
        'business': business,
        'date_options': date_options,
    }
    
    return render(request, 'core/block_time.html', context)


@login_required
def create_appointment_manual_view(request, business_slug):
    """
    Vista para que el BusinessOwner cree citas manualmente (para clientes que llaman).
    Solo para el día actual, solo con teléfono.
    """
    business = get_object_or_404(Business, slug=business_slug, is_active=True)
    
    # Verificar que el usuario sea el dueño del negocio
    if business.owner != request.user:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('admin:index')
    
    services = Service.objects.filter(business=business, is_active=True)
    
    # Solo día actual
    today = business.get_local_today()
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            client_phone = request.POST.get('client_phone', '').strip()
            client_first_name = request.POST.get('client_first_name', '').strip()
            client_last_name = request.POST.get('client_last_name', '').strip()
            service_id = request.POST.get('service_id')
            time_str = request.POST.get('time')
            notes = request.POST.get('notes', '').strip()
            
            # Validaciones
            if not client_phone:
                messages.error(request, 'Debes proporcionar el teléfono del cliente.')
                return render(request, 'core/create_appointment_manual.html', {
                    'business': business,
                    'services': services,
                    'selected_date': today,
                })
            
            if not service_id:
                messages.error(request, 'Debes seleccionar un servicio.')
                return render(request, 'core/create_appointment_manual.html', {
                    'business': business,
                    'services': services,
                    'selected_date': today,
                })
            
            if not time_str:
                messages.error(request, 'Debes seleccionar una hora.')
                return render(request, 'core/create_appointment_manual.html', {
                    'business': business,
                    'services': services,
                    'selected_date': today,
                })
            
            # Obtener o crear cliente por teléfono
            try:
                client = CustomUser.objects.get(phone=client_phone)
                # Actualizar datos si se proporcionaron
                if client_first_name:
                    client.first_name = client_first_name
                if client_last_name:
                    client.last_name = client_last_name
                client.save()
            except CustomUser.DoesNotExist:
                # Crear cliente con email temporal basado en teléfono
                temp_email = f"cliente_{client_phone.replace('+', '').replace('-', '').replace(' ', '')}@temp.com"
                import secrets
                temp_password = secrets.token_urlsafe(8)
                client = CustomUser.objects.create_user(
                    email=temp_email,
                    password=temp_password,
                    first_name=client_first_name,
                    last_name=client_last_name,
                    phone=client_phone,
                    is_owner=False
                )
            
            # Obtener servicio
            service = Service.objects.get(id=service_id, business=business, is_active=True)
            
            # Crear datetime para hoy
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            start_time = timezone.make_aware(datetime.combine(today, time_obj))
            
            # Verificar disponibilidad
            if not AvailabilityService.is_slot_available(business, service, start_time):
                messages.error(request, 'Este horario ya no está disponible. Por favor, selecciona otro.')
                return render(request, 'core/create_appointment_manual.html', {
                    'business': business,
                    'services': services,
                    'selected_date': today,
                })
            
            # Crear la cita
            appointment = Appointment.objects.create(
                business=business,
                client=client,
                service=service,
                start_time=start_time,
                status='confirmed',  # Las citas creadas manualmente se confirman automáticamente
                notes=notes
            )
            
            messages.success(request, f'Cita creada exitosamente para {client.get_full_name() or client.phone} hoy a las {time_str}.')
            return redirect('core:dashboard', business_slug=business.slug)
            
        except Service.DoesNotExist:
            messages.error(request, 'Servicio no encontrado.')
        except ValueError as e:
            messages.error(request, f'Error en el formato de hora: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error al crear la cita: {str(e)}')
    
    context = {
        'business': business,
        'services': services,
        'selected_date': today,
    }
    
    return render(request, 'core/create_appointment_manual.html', context)


@login_required
def get_dashboard_appointments_api(request, business_slug):
    """
    API endpoint para obtener las citas del dashboard en formato JSON.
    Usado para actualización en tiempo real.
    """
    try:
        business = get_object_or_404(Business, slug=business_slug, is_active=True)
        
        # Verificar que el usuario sea el dueño del negocio
        if business.owner != request.user:
            return JsonResponse({'error': 'No autorizado'}, status=403)
        
        # Obtener fecha seleccionada (por defecto hoy)
        selected_date_str = request.GET.get('date')
        business_today = business.get_local_today()
        
        if selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = business_today
        else:
            selected_date = business_today
        
        # Obtener citas del día seleccionado
        appointments = Appointment.objects.filter(
            business=business,
            start_time__date=selected_date
        ).select_related('client', 'service').order_by('start_time')
        
        # Estadísticas
        total = appointments.count()
        confirmed = appointments.filter(status='confirmed').count()
        pending = appointments.filter(status='pending').count()
        completed = appointments.filter(status='completed').count()
        
        # Generar todas las horas del día para el calendario (igual que en dashboard_view)
        schedule_config = business.schedule_config or business.get_default_schedule()
        weekday = selected_date.weekday()
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_key = day_names[weekday]
        day_config = schedule_config.get(day_key, {})
        
        open_time_str = day_config.get('open', '09:00') if day_config.get('enabled', False) else '09:00'
        close_time_str = day_config.get('close', '20:00') if day_config.get('enabled', False) else '20:00'
        
        open_hour, open_minute = map(int, open_time_str.split(':'))
        close_hour, close_minute = map(int, close_time_str.split(':'))
        
        time_slots = []
        current_hour = open_hour
        current_minute = open_minute
        
        while current_hour < close_hour or (current_hour == close_hour and current_minute < close_minute):
            time_str = f"{current_hour:02d}:{current_minute:02d}"
            time_slots.append({
                'time': time_str,
                'hour': current_hour,
                'minute': current_minute
            })
            
            current_minute += 15
            if current_minute >= 60:
                current_minute = 0
                current_hour += 1
        
        # Crear diccionario de citas por hora
        appointments_by_time = {}
        for apt in appointments:
            apt_time = apt.start_time.time()
            time_key = f"{apt_time.hour:02d}:{apt_time.minute:02d}"
            if time_key not in appointments_by_time:
                appointments_by_time[time_key] = apt
        
        # Formatear slots con citas para JSON
        time_slots_data = []
        for slot in time_slots:
            appointment = appointments_by_time.get(slot['time'])
            if appointment and appointment.start_time.strftime('%H:%M') == slot['time']:
                time_slots_data.append({
                    'time': slot['time'],
                    'appointment': {
                        'id': appointment.id,
                        'is_block': appointment.is_block,
                        'client_name': appointment.client.get_full_name() if appointment.client else 'N/A',
                        'client_email': appointment.client.email if appointment.client else 'N/A',
                        'client_phone': appointment.client.phone if appointment.client and appointment.client.phone else None,
                        'service_name': appointment.service.name if appointment.service else 'Horario bloqueado',
                        'service_duration': appointment.service.duration_minutes if appointment.service else None,
                        'service_price': str(appointment.service.price) if appointment.service else None,
                        'start_time': appointment.start_time.strftime('%H:%M'),
                        'end_time': appointment.end_time.strftime('%H:%M'),
                        'start_datetime': appointment.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'status': appointment.status,
                        'status_display': appointment.get_status_display(),
                        'notes': appointment.notes or '',
                    }
                })
            else:
                time_slots_data.append({
                    'time': slot['time'],
                    'appointment': None
                })
        
        return JsonResponse({
            'success': True,
            'date': selected_date.strftime('%Y-%m-%d'),
            'date_display': selected_date.strftime('%d/%m/%Y'),
            'stats': {
                'total': total,
                'confirmed': confirmed,
                'pending': pending,
                'completed': completed,
            },
            'time_slots': time_slots_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def edit_site_view(request, business_slug):
    """
    Vista para que el BusinessOwner edite su landing page.
    """
    business = get_object_or_404(Business, slug=business_slug, is_active=True)
    
    # Verificar que el usuario sea el dueño del negocio
    if business.owner != request.user:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('admin:index')
    
    # Convertir gallery_json a formato legible para el textarea
    gallery_text = json.dumps(business.gallery_json, indent=2, ensure_ascii=False) if business.gallery_json else "[]"
    
    # Obtener imágenes subidas de la galería
    gallery_images = GalleryImage.objects.filter(business=business).order_by('order', '-created_at')
    
    context = {
        'business': business,
        'gallery_text': gallery_text,
        'gallery_images': gallery_images,
    }
    
    return render(request, 'core/edit_site.html', context)


@login_required
def update_business_field_api(request, business_slug):
    """
    API endpoint para actualizar campos individuales del negocio.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    business = get_object_or_404(Business, slug=business_slug, is_active=True)
    
    # Verificar que el usuario sea el dueño del negocio
    if business.owner != request.user:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        field_name = data.get('field_name')
        field_value = data.get('field_value')
        
        if not field_name:
            return JsonResponse({'success': False, 'error': 'Campo no especificado'}, status=400)
        
        # Validar y actualizar el campo correspondiente
        valid_fields = [
            'description', 'hero_image_url', 'logo_url', 'primary_color',
            'instagram_url', 'facebook_url', 'gallery_json', 'capacity'
        ]
        
        if field_name not in valid_fields:
            return JsonResponse({'success': False, 'error': 'Campo inválido'}, status=400)
        
        # Actualizar el campo
        if field_name == 'capacity':
            # Validar que capacity sea un entero positivo
            try:
                capacity_value = int(field_value)
                if capacity_value < 1:
                    return JsonResponse({'success': False, 'error': 'La capacidad debe ser al menos 1'}, status=400)
                business.capacity = capacity_value
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'La capacidad debe ser un número entero válido'}, status=400)
        elif field_name == 'gallery_json':
            # Procesar JSON para la galería
            if field_value and field_value.strip():
                try:
                    gallery_list = json.loads(field_value)
                    if isinstance(gallery_list, list):
                        business.gallery_json = gallery_list
                    else:
                        return JsonResponse({'success': False, 'error': 'El formato de la galería debe ser un array JSON.'}, status=400)
                except json.JSONDecodeError as e:
                    return JsonResponse({'success': False, 'error': f'Error en el formato JSON: {str(e)}'}, status=400)
            else:
                business.gallery_json = []
        else:
            # Para otros campos, asignar directamente
            setattr(business, field_name, field_value or '')
        
        business.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{field_name.replace("_", " ").title()} guardado exitosamente.',
            'field_name': field_name,
            'field_value': field_value
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def upload_gallery_image(request, business_slug):
    """
    Vista para subir imágenes a la galería del negocio.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    business = get_object_or_404(Business, slug=business_slug, is_active=True)
    
    # Verificar que el usuario sea el dueño del negocio
    if business.owner != request.user:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    try:
        if 'image' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se proporcionó ninguna imagen'}, status=400)
        
        image_file = request.FILES['image']
        caption = request.POST.get('caption', '')
        
        # Validar que sea una imagen
        if not image_file.content_type.startswith('image/'):
            return JsonResponse({'success': False, 'error': 'El archivo debe ser una imagen'}, status=400)
        
        # Crear la imagen de galería
        gallery_image = GalleryImage.objects.create(
            business=business,
            image=image_file,
            caption=caption
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Imagen subida exitosamente',
            'image_id': gallery_image.id,
            'image_url': gallery_image.image.url,
            'caption': gallery_image.caption or ''
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def delete_gallery_image(request, business_slug, image_id):
    """
    Vista para eliminar una imagen de la galería.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    business = get_object_or_404(Business, slug=business_slug, is_active=True)
    
    # Verificar que el usuario sea el dueño del negocio
    if business.owner != request.user:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    try:
        gallery_image = get_object_or_404(GalleryImage, id=image_id, business=business)
        gallery_image.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Imagen eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def get_available_slots_api(request, business_slug):
    """
    API endpoint para obtener slots disponibles para un servicio y fecha.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        business = get_object_or_404(Business, slug=business_slug, is_active=True)
        data = json.loads(request.body)
        
        service_id = data.get('service_id')
        date_str = data.get('date')
        
        if not service_id or not date_str:
            return JsonResponse({'error': 'service_id y date son requeridos'}, status=400)
        
        service = Service.objects.get(id=service_id, business=business, is_active=True)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Obtener slots disponibles usando el servicio
        available_slots = AvailabilityService.get_available_slots(business, service, date_obj)
        
        # Formatear slots para el frontend
        slots_formatted = [
            {
                'datetime': slot.strftime('%Y-%m-%d %H:%M:%S'),
                'time': slot.strftime('%H:%M'),
            }
            for slot in available_slots
        ]
        
        return JsonResponse({
            'success': True,
            'slots': slots_formatted,
            'service_duration': service.duration_minutes
        })
        
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': f'Error en formato de fecha: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al obtener slots: {str(e)}'}, status=500)
