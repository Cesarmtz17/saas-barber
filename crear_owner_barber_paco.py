"""
Script para crear un usuario owner específico para barber-paco.
Ejecuta: python crear_owner_barber_paco.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saasBarber.settings')
django.setup()

from core.models import Business, CustomUser

def crear_owner():
    slug = "barber-paco"
    email = "paco@barber-paco.com"
    password = "paco123"
    
    try:
        business = Business.objects.get(slug=slug, is_active=True)
        
        # Verificar si el usuario ya existe
        try:
            user = CustomUser.objects.get(email=email)
            print(f"Usuario {email} ya existe. Actualizando...")
            user.is_owner = True
            user.is_staff = True
            user.set_password(password)
            user.save()
        except CustomUser.DoesNotExist:
            # Crear nuevo usuario
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name="Paco",
                last_name="Barber",
                is_owner=True,
                is_staff=True
            )
            print(f"Usuario {email} creado exitosamente.")
        
        # Asociar al negocio
        business.owner = user
        business.save()
        
        print("\n" + "="*60)
        print("USUARIO OWNER CREADO PARA BARBER-PACO")
        print("="*60)
        print(f"Negocio: {business.name}")
        print(f"Owner: {user.email}")
        print(f"Nombre: {user.get_full_name()}")
        print(f"Es Propietario: {user.is_owner}")
        print(f"Puede acceder al admin: {user.is_staff}")
        print("="*60)
        print(f"\nCREDENCIALES PARA ACCEDER:")
        print(f"  Email: {email}")
        print(f"  Contraseña: {password}")
        print("="*60)
        print(f"\nURLs:")
        print(f"  - Página pública: http://127.0.0.1:8000/{business.slug}/")
        print(f"  - Dashboard: http://127.0.0.1:8000/{business.slug}/dashboard/")
        print(f"  - Admin: http://127.0.0.1:8000/admin/")
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
    crear_owner()
