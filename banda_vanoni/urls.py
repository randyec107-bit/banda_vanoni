from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.models import LogEntry
from django.utils import timezone
from django.contrib.auth.views import LogoutView

# ------------------ Notificaciones ------------------
@csrf_exempt
def get_new_notifications(request):
    """Obtener notificaciones nuevas desde el último check"""
    after_time = request.GET.get('after_time', timezone.now().isoformat())
    
    try:
        new_logs = LogEntry.objects.filter(
            action_time__gt=after_time
        ).select_related('content_type', 'user')[:10]
        
        notifications = []
        latest_time = after_time
        
        for log in new_logs:
            notifications.append({
                'object_repr': log.object_repr,
                'user': log.user.username if log.user else 'Sistema',
                'action_time': log.action_time.isoformat(),
                'is_addition': log.is_addition(),
                'is_change': log.is_change(),
                'is_deletion': log.is_deletion(),
                'admin_url': log.get_admin_url() if hasattr(log, 'get_admin_url') else '#'
            })
            if log.action_time.isoformat() > latest_time:
                latest_time = log.action_time.isoformat()
        
        return JsonResponse({
            'success': True,
            'notifications': notifications,
            'latest_time': latest_time
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
def get_all_notifications(request):
    """Obtener todas las notificaciones recientes"""
    try:
        logs = LogEntry.objects.all().select_related('content_type', 'user').order_by('-action_time')[:10]
        
        notifications = []
        for log in logs:
            notifications.append({
                'object_repr': log.object_repr,
                'user': log.user.username if log.user else 'Sistema',
                'action_time': log.action_time.isoformat(),
                'is_addition': log.is_addition(),
                'is_change': log.is_change(),
                'is_deletion': log.is_deletion(),
                'admin_url': log.get_admin_url() if hasattr(log, 'get_admin_url') else '#'
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ------------------ Redirección raíz ------------------
def redirect_to_admin_login(request):
    """Redirige al login del admin de Django"""
    return RedirectView.as_view(url='/admin/login/', permanent=False)(request)

# ------------------ URLs ------------------
urlpatterns = [
    # Redirigir la raíz al login del admin
    path('', redirect_to_admin_login, name='root_redirect'),

    # Dashboard accesible con nombre 'index' para reverse/url
    path('dashboard/', TemplateView.as_view(template_name='dashboard/index.html'), name='index'),

    # Admin de Django
    path('admin/', admin.site.urls),

    # Apps propias
    path("pedidos/", include("pedidos.urls")),
    path("adquisiciones/", include("adquisiciones.urls")),
    path("productos/", include("productos.urls")),
    path("clientes/", include("clientes.urls")),
    path("facturacion/", include("facturacion.urls")),
    path("inventario/", include("inventario.urls")),
    path("proveedores/", include("proveedores.urls")),
    path('dashboard/', include('dashboard.urls')),
    
    # Logout configurado
    path('logout/', LogoutView.as_view(next_page='/admin/login/'), name='logout'),

    # Librerías externas
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    
    # URLs de notificaciones
    path('admin/get-new-notifications/', get_new_notifications, name='get_new_notifications'),
    path('admin/get-all-notifications/', get_all_notifications, name='get_all_notifications'),
]
