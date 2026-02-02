"""
Script para actualizar la zona horaria de barber-paco a America/Monterrey.
Ejecuta: python actualizar_timezone_barber_paco.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saasBarber.settings')
django.setup()

from core.models import Business

def actualizar_timezone():
    slug = "barber-paco"
    
    try:
        business = Business.objects.get(slug=slug, is_active=True)
        business.timezone = 'America/Monterrey'
        business.save()
        
        print("\n" + "="*60)
        print("ZONA HORARIA ACTUALIZADA")
        print("="*60)
        print(f"Negocio: {business.name}")
        print(f"Zona Horaria: {business.timezone}")
        print("="*60 + "\n")
            
    except Business.DoesNotExist:
        print(f"\nERROR: No se encontró un negocio con slug '{slug}'")

if __name__ == "__main__":
    actualizar_timezone()
