"""
Script para verificar el owner de barber-paco.
Ejecuta: python ver_owner_barber_paco.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saasBarber.settings')
django.setup()

from core.models import Business, CustomUser

def ver_owner():
    slug = "barber-paco"
    
    try:
        business = Business.objects.get(slug=slug, is_active=True)
        print("\n" + "="*60)
        print(f"NEGOCIO: {business.name}")
        print("="*60)
        print(f"Slug: {business.slug}")
        print(f"Owner actual: {business.owner.email}")
        print(f"Owner es propietario: {business.owner.is_owner}")
        print(f"Owner puede acceder al admin: {business.owner.is_staff}")
        print("="*60)
        print(f"\nCREDENCIALES PARA ACCEDER AL DASHBOARD:")
        print(f"  Email: {business.owner.email}")
        print(f"  URL: http://127.0.0.1:8000/{business.slug}/dashboard/")
        print("="*60)
        print(f"\nSi necesitas cambiar la contraseña o crear un nuevo owner,")
        print(f"ve al admin: http://127.0.0.1:8000/admin/core/business/")
        print(f"y edita el negocio '{business.name}' para cambiar el owner.")
        print("="*60 + "\n")
            
    except Business.DoesNotExist:
        print(f"\nERROR: No se encontró un negocio con slug '{slug}'")
        print("\nNegocios disponibles:")
        businesses = Business.objects.filter(is_active=True)
        if businesses.exists():
            for b in businesses:
                print(f"  - {b.slug} ({b.name}) - Owner: {b.owner.email}")
        else:
            print("  No hay negocios registrados.")

if __name__ == "__main__":
    ver_owner()
