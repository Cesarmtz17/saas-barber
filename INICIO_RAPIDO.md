# 🚀 Inicio Rápido - SaaS Barber

## Pasos para Ejecutar el Proyecto

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Crear Migraciones y Aplicarlas

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Crear Superusuario (Opcional, para acceder al admin)

```bash
python manage.py createsuperuser
```

### 4. Iniciar el Servidor de Desarrollo

```bash
python manage.py runserver
```

### 5. Acceder a la Aplicación

Una vez que el servidor esté corriendo, verás algo como:

```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**URLs Disponibles:**

- **Admin de Django**: http://127.0.0.1:8000/admin/
- **Dashboard del Dueño**: http://127.0.0.1:8000/dashboard/
- **Página de Reserva Pública**: http://127.0.0.1:8000/reserva/<slug-del-negocio>/

## Configuración Inicial

### Crear un Negocio de Prueba

1. Ve a http://127.0.0.1:8000/admin/
2. Inicia sesión con tu superusuario
3. Crea un usuario con `is_owner=True`
4. Crea un Business asociado a ese usuario
5. Configura los horarios en `schedule_config` (formato JSON)
6. Crea algunos Services para ese Business

### Ejemplo de schedule_config:

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

### Probar la Aplicación

1. **Dashboard**: Inicia sesión como dueño y ve a `/dashboard/`
2. **Reserva Pública**: Usa el slug de tu negocio: `/reserva/mi-negocio/`
3. **Bloquear Horario**: Desde el dashboard, click en "Bloquear Horario"

## Notas Importantes

- El servidor se recarga automáticamente cuando cambias código (hot reload)
- Para detener el servidor: Presiona `CTRL+C` en la terminal
- Por defecto corre en el puerto 8000
- Para cambiar el puerto: `python manage.py runserver 8080`
