"""
Script para crear un usuario propietario desde la terminal.
Ejecuta: python crear_usuario_owner.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saasBarber.settings')
django.setup()

from core.models import CustomUser

def crear_usuario_owner():
    email = input("Email del usuario propietario: ")
    password = input("Contraseña: ")
    first_name = input("Nombre (opcional, presiona Enter para omitir): ") or ""
    last_name = input("Apellido (opcional, presiona Enter para omitir): ") or ""
    
    # Verificar si el usuario ya existe
    if CustomUser.objects.filter(email=email).exists():
        print(f"❌ El usuario {email} ya existe.")
        return
    
    # Crear usuario
    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_owner=True,
        is_staff=True  # Para que pueda acceder al admin
    )
    
    print(f"\n✅ Usuario propietario creado exitosamente!")
    print(f"   Email: {user.email}")
    print(f"   Es Propietario: {user.is_owner}")
    print(f"   Puede acceder al admin: {user.is_staff}")
    print(f"\n💡 Ahora puedes iniciar sesión en el admin con este usuario.")

if __name__ == "__main__":
    crear_usuario_owner()
