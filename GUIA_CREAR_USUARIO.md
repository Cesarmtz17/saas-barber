# 📝 Guía: Crear Usuario Propietario (is_owner)

## Pasos Detallados

### 1. Acceder al Admin de Django

1. Abre tu navegador
2. Ve a: **http://127.0.0.1:8000/admin/**
3. Inicia sesión con tu superusuario (el que creaste con `createsuperuser`)

### 2. Crear un Usuario Propietario

1. En el panel del admin, busca la sección **"CORE"** o **"USUARIOS"**
2. Haz clic en **"Usuarios"** o **"Custom Users"**
3. Haz clic en el botón **"+ AÑADIR USUARIO"** (arriba a la derecha)

### 3. Completar el Formulario

**Campos obligatorios:**
- **Email**: `owner@example.com` (o el email que prefieras)
- **Contraseña**: Escribe una contraseña
- **Confirmar contraseña**: Vuelve a escribir la misma contraseña

**Campos importantes:**
- ✅ **Marca la casilla "Es Propietario"** (is_owner) - **ESTO ES CLAVE**
- Opcional: Nombre, Apellido, Teléfono

**Permisos:**
- Si quieres que también pueda acceder al admin, marca **"Es Staff"**
- Si quieres que tenga todos los permisos, marca **"Es Superusuario"** (pero no es necesario)

### 4. Guardar

1. Haz clic en **"GUARDAR"** (botón azul abajo)
2. ¡Listo! Ya tienes un usuario propietario

## Alternativa: Crear desde la Terminal

Si prefieres crear el usuario desde la terminal:

```bash
python manage.py shell
```

Luego ejecuta:

```python
from core.models import CustomUser

# Crear usuario propietario
user = CustomUser.objects.create_user(
    email='owner@example.com',
    password='tu_contraseña_aqui',
    is_owner=True,
    is_staff=True  # Opcional: para que pueda acceder al admin
)

print(f"Usuario creado: {user.email}")
```

Presiona `Ctrl+Z` y luego `Enter` para salir del shell.

## Verificar que Funcionó

1. Cierra sesión del admin
2. Inicia sesión con el nuevo usuario propietario
3. Ve a: **http://127.0.0.1:8000/dashboard/**
4. Si funciona, verás el dashboard (aunque probablemente diga que no tienes negocio aún)

## Próximo Paso: Crear un Business

Después de crear el usuario propietario, necesitas crear un Business:

1. En el admin, ve a **"Negocios"** o **"Businesses"**
2. Haz clic en **"+ AÑADIR NEGOCIO"**
3. Completa:
   - **Propietario**: Selecciona el usuario que acabas de crear
   - **Nombre del Negocio**: Ej: "Barbería Paco"
   - **Slug**: Se genera automáticamente (o puedes personalizarlo)
   - **Dirección**: Opcional
   - **Schedule Config**: Usa este formato JSON:
     ```json
     {
       "monday": {"open": "09:00", "close": "18:00", "enabled": true},
       "tuesday": {"open": "09:00", "close": "18:00", "enabled": true},
       "wednesday": {"open": "09:00", "close": "18:00", "enabled": true},
       "thursday": {"open": "09:00", "close": "18:00", "enabled": true},
       "friday": {"open": "09:00", "close": "18:00", "enabled": true},
       "saturday": {"open": "09:00", "close": "14:00", "enabled": true},
       "sunday": {"open": "09:00", "close": "14:00", "enabled": false}
     }
     ```
4. Guarda

¡Ahora ya puedes usar el dashboard!
