from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin import AdminSite
from django.shortcuts import redirect

class DashboardAdminSite(AdminSite):
    site_header = "Sistema Empresarial"
    site_title = "Panel de Administración"
    index_title = "Dashboard Principal"
    
    def get_app_list(self, request):
        """
        Agrega el dashboard al menú de apps
        """
        app_list = super().get_app_list(request)
        
        
        dashboard_app = {
            'name': '📊 DASHBOARD',
            'app_label': 'dashboard',
            'app_url': '/',
            'has_module_perms': True,
            'models': [
                {
                    'name': 'Dashboard Principal',
                    'object_name': 'dashboard',
                    'admin_url': '/',
                    'view_only': True,
                }
            ]
        }
        
        
        app_list.insert(0, dashboard_app)
        return app_list


dashboard_admin_site = DashboardAdminSite(name='dashboard_admin')

