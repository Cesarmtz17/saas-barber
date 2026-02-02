"""
Script para crear un superusuario automáticamente.
Ejecuta: python crear_superusuario.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saasBarber.settings')
django.setup()

from core.models import CustomUser

def crear_superusuario():
    email = "admin@saasbarber.com"
    password = "admin123"  # Cambia esta contraseña después
    
    # Verificar si ya existe
    if CustomUser.objects.filter(email=email).exists():
        user = CustomUser.objects.get(email=email)
        # Actualizar para asegurar que sea superusuario y propietario
        user.is_superuser = True
        user.is_staff = True
        user.is_owner = True
        user.set_password(password)  # Actualizar contraseña
        user.save()
        print("\n" + "="*60)
        print("USUARIO ACTUALIZADO EXITOSAMENTE!")
        print("="*60)
        print(f"Email: {email}")
        print(f"Contrasena: {password}")
        print(f"Es Superusuario: Si")
        print(f"Es Propietario: Si")
        print("="*60)
        print(f"\nAhora puedes iniciar sesion en: http://127.0.0.1:8000/admin/")
        print("="*60 + "\n")
        return
    
    # Crear superusuario nuevo
    try:
        user = CustomUser.objects.create_superuser(
            email=email,
            password=password,
            is_owner=True  # También lo hacemos propietario
        )
        print("\n" + "="*60)
        print("SUPERUSUARIO CREADO EXITOSAMENTE!")
        print("="*60)
        print(f"Email: {email}")
        print(f"Contrasena: {password}")
        print(f"Es Superusuario: Si")
        print(f"Es Propietario: Si")
        print("="*60)
        print(f"\nAhora puedes iniciar sesion en: http://127.0.0.1:8000/admin/")
        print("="*60 + "\n")
    except Exception as e:
        print(f"Error al crear superusuario: {str(e)}")

if __name__ == "__main__":
    crear_superusuario()
