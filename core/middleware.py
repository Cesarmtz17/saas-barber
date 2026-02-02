"""
Middleware para redirigir automáticamente a los owners a su dashboard.
"""
from django.shortcuts import redirect
from django.urls import reverse
from .models import Business


class OwnerRedirectMiddleware:
    """
    Redirige automáticamente a los owners a su dashboard después del login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Si el usuario está autenticado, es owner, y está en el admin (después del login)
        if (request.user.is_authenticated and 
            hasattr(request.user, 'is_owner') and
            request.user.is_owner and 
            request.path == '/admin/' and
            not request.GET.get('next')):
            
            # Intentar obtener el negocio del usuario
            try:
                business = Business.objects.get(owner=request.user, is_active=True)
                # Redirigir al dashboard del negocio
                from django.shortcuts import redirect
                from django.urls import reverse
                return redirect('core:dashboard', business_slug=business.slug)
            except Business.DoesNotExist:
                pass
            except Business.MultipleObjectsReturned:
                business = Business.objects.filter(owner=request.user, is_active=True).first()
                if business:
                    from django.shortcuts import redirect
                    return redirect('core:dashboard', business_slug=business.slug)
        
        return response
