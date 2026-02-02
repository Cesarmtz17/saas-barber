"""
Script para actualizar el horario de cierre del negocio 'barber-paco' a las 20:00 (8pm).
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saasBarber.settings')
django.setup()

from core.models import Business

def actualizar_horario():
    """Actualiza el horario de cierre a las 20:00 para todos los días."""
    try:
        business = Business.objects.get(slug='barber-paco')
        
        # Obtener configuración actual o usar la por defecto
        schedule_config = business.schedule_config if business.schedule_config else business.get_default_schedule()
        
        # Actualizar horario de cierre a las 20:00 para todos los días habilitados
        dias_semana = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for dia in dias_semana:
            if dia in schedule_config:
                # Mantener la hora de apertura y enabled, solo cambiar close
                schedule_config[dia]['close'] = '20:00'
            else:
                # Si no existe, crear con horario estándar
                schedule_config[dia] = {
                    'open': '09:00',
                    'close': '20:00',
                    'enabled': True if dia not in ['saturday', 'sunday'] else (True if dia == 'saturday' else False)
                }
        
        # Guardar cambios
        business.schedule_config = schedule_config
        business.save()
        
        print("=" * 60)
        print("HORARIO ACTUALIZADO EXITOSAMENTE")
        print("=" * 60)
        print(f"Negocio: {business.name}")
        print(f"Slug: {business.slug}")
        print("\nNuevo horario de cierre: 20:00 (8pm)")
        print("\nHorarios configurados:")
        dias_nombres = {
            'monday': 'Lunes',
            'tuesday': 'Martes',
            'wednesday': 'Miércoles',
            'thursday': 'Jueves',
            'friday': 'Viernes',
            'saturday': 'Sábado',
            'sunday': 'Domingo',
        }
        for dia_key, dia_nombre in dias_nombres.items():
            dia_config = schedule_config.get(dia_key, {})
            if dia_config.get('enabled', False):
                print(f"  {dia_nombre}: {dia_config.get('open', 'N/A')} - {dia_config.get('close', 'N/A')}")
            else:
                print(f"  {dia_nombre}: Cerrado")
        print("=" * 60)
        
    except Business.DoesNotExist:
        print("ERROR: No se encontró el negocio con slug 'barber-paco'")
        print("Asegúrate de que el negocio existe en la base de datos.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR al actualizar el horario: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    actualizar_horario()
