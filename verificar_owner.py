"""
Script para verificar y crear el usuario owner de un negocio.
Ejecuta: python verificar_owner.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saasBarber.settings')
django.setup()

from core.models import Business, CustomUser

def verificar_owner():
    slug = input("Slug del negocio (ej: barber-paco): ").strip()
    
    try:
        business = Business.objects.get(slug=slug, is_active=True)
        print(f"\n{'='*60}")
        print(f"NEGOCIO ENCONTRADO: {business.name}")
        print(f"{'='*60}")
        print(f"Slug: {business.slug}")
        print(f"Owner actual: {business.owner.email}")
        print(f"Owner es propietario: {business.owner.is_owner}")
        print(f"{'='*60}\n")
        
        respuesta = input("¿Deseas cambiar el owner o crear uno nuevo? (s/n): ").lower()
        
        if respuesta == 's':
            email = input("Email del nuevo owner: ").strip()
            password = input("Contraseña: ").strip()
            
            # Verificar si el usuario existe
            try:
                user = CustomUser.objects.get(email=email)
                print(f"\nUsuario {email} ya existe. Actualizando...")
                user.is_owner = True
                user.is_staff = True
                user.set_password(password)
                user.save()
            except CustomUser.DoesNotExist:
                # Crear nuevo usuario
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    is_owner=True,
                    is_staff=True
                )
                print(f"\nUsuario {email} creado exitosamente.")
            
            # Asociar al negocio
            business.owner = user
            business.save()
            
            print(f"\n{'='*60}")
            print("CONFIGURACION COMPLETADA!")
            print(f"{'='*60}")
            print(f"Negocio: {business.name}")
            print(f"Owner: {user.email}")
            print(f"Es Propietario: {user.is_owner}")
            print(f"Puede acceder al admin: {user.is_staff}")
            print(f"\nURLs:")
            print(f"  - Página pública: http://127.0.0.1:8000/{business.slug}/")
            print(f"  - Dashboard: http://127.0.0.1:8000/{business.slug}/dashboard/")
            print(f"\nCredenciales para iniciar sesión:")
            print(f"  Email: {user.email}")
            print(f"  Contraseña: {password}")
            print(f"{'='*60}\n")
        else:
            print(f"\nPara acceder al dashboard de {business.name}:")
            print(f"  Email: {business.owner.email}")
            print(f"  URL: http://127.0.0.1:8000/{business.slug}/dashboard/")
            print(f"\nSi no recuerdas la contraseña, puedes cambiarla desde el admin.")
            
    except Business.DoesNotExist:
        print(f"\nERROR: No se encontró un negocio con slug '{slug}'")
        print("\nNegocios disponibles:")
        businesses = Business.objects.filter(is_active=True)
        for b in businesses:
            print(f"  - {b.slug} ({b.name}) - Owner: {b.owner.email}")

if __name__ == "__main__":
    verificar_owner()
