from django.contrib.staticfiles import finders  # Añade este import
import base64
import os
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import render, get_object_or_404
from django.contrib import admin
from django.utils.html import format_html
from datetime import date, timedelta
from .models import Chofer, Vehiculo, Rendicion, Viaje
from django.contrib import messages
from django.template.loader import render_to_string
import tempfile
from weasyprint import HTML  # Asegurate de tener instalado weasyprint
from django.templatetags.static import static
from django.contrib.staticfiles.finders import find
from django.conf import settings

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'alias', 'patente', 'marca', 'modelo', 'año',
        'seguro_empresa', 'estado_seguro', 'estado_vtv',
        'titular_uber', 'titular_cabify', 'activo'
    )
    
    search_fields = ('alias', 'patente', 'marca', 'modelo', 'seguro_empresa')
    list_filter = ('activo', 'seguro_empresa')

    def estado_seguro(self, obj):
        return self._formatear_estado_fecha(obj.seguro_vencimiento)
    estado_seguro.short_description = "Seguro"

    def estado_vtv(self, obj):
        return self._formatear_estado_fecha(obj.vtv_vencimiento)
    estado_vtv.short_description = "VTV"

    def _formatear_estado_fecha(self, fecha):
        hoy = date.today()
        if fecha:
            if fecha < hoy:
                return format_html('<span style="color: red; font-weight: bold;">VENCIDO</span>')
            elif fecha <= hoy + timedelta(days=30):
                return format_html('<span style="color: orange; font-weight: bold;">PRONTO A VENCER</span>')
            else:
                return format_html('<span style="color: green;">Vigente</span>')
        return format_html('<span style="color: gray;">Sin fecha</span>')



class ViajeInline(admin.TabularInline):
    model = Viaje
    extra = 0

    def has_add_permission(self, request, obj):
        return not obj.cerrada if obj else True

    def has_change_permission(self, request, obj=None):
        return not obj.cerrada if obj else True

    def has_delete_permission(self, request, obj=None):
        return not obj.cerrada if obj else True



@admin.register(Rendicion)
class RendicionAdmin(admin.ModelAdmin):
    list_display = ('chofer', 'vehiculo', 'fecha_creacion', 'fecha_cierre', 'cerrada')
    inlines = [ViajeInline]
    actions = ['cerrar_y_generar_pdf']
    list_filter = ('chofer', 'vehiculo', 'cerrada')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:rendicion_id>/cerrar/', self.admin_site.admin_view(self.cerrar_rendicion_view), name='cerrar_rendicion'),
        ]
        return custom_urls + urls
		
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.cerrada:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_change_permission(self, request, obj=None):
        if obj and obj.cerrada:
            return False  # Bloquea edición total
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.cerrada:
            return False  # No se puede borrar una cerrada
        return super().has_delete_permission(request, obj)
	
    def cerrar_y_generar_pdf(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Seleccioná solo una rendición para cerrar y generar PDF.", level=messages.ERROR)
            return

        rendicion = queryset.first()
        return HttpResponseRedirect(f'{rendicion.id}/cerrar/')
      
    cerrar_y_generar_pdf.short_description = "Cerrar rendición y generar PDF"

    def cerrar_rendicion_view(self, request, rendicion_id):
        rendicion = get_object_or_404(Rendicion, pk=rendicion_id)
        rendicion.fecha_cierre = rendicion.fecha_cierre or date.today()
        rendicion.cerrada = True
        rendicion.save()

        # Obtener la ruta del logo usando finders
        logo_path = finders.find('images/corpux.png')  # Asegúrate de que la ruta es correcta
        
        if not logo_path:
            raise FileNotFoundError(
                "No se encontró el logo en static/images/corpux.png. "
                "Verifica la ruta y ejecuta 'collectstatic' si es necesario."
            )
            # Método 100% efectivo para obtener el logo
        try:
            logo_path = staticfiles_storage.path('images/corpux.png')
            with open(logo_path, "rb") as f:
                logo_data = f.read()
            logo_base64 = base64.b64encode(logo_data).decode('utf-8')
    
        except Exception as e:
            logo_base64 = ""  # Fallback seguro
            print(f"Error cargando logo: {str(e)}")

        logo_path = find('images/corpux.png')  # Busca en todos los staticfiles_dirs
        if not logo_path:
            raise FileNotFoundError("No se encontró el logo en static/images/corpux.png")
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        
        logo_absolute_url = request.build_absolute_uri(static('images/corpux.png'))
        print(f"URL del logo: {logo_absolute_url}") 
        
        # Convertir logo a Base64
        with open(logo_path, "rb") as logo_file:
            logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
            
        # Render PDF
        viajes = rendicion.viajes.all()
        html_string = render_to_string('pdf/rendicion.html', {
            'logo_base64': logo_base64,
            'logo_url': logo_absolute_url,
            'rendicion': rendicion,
            'viajes': viajes,
            'total_ingresos': rendicion.total_ingresos,  # Nuevo
            'total_egresos': rendicion.total_egresos,    # Nuevo
            'total_neto': rendicion.total_neto,          # Nuevo
        })
        pdf_file = HTML(
			string=html_string,
			base_url=request.build_absolute_uri('/')        
        ).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="rendicion_{rendicion.id}.pdf"'
        return response
    
   
@admin.register(Viaje)
class ViajeAdmin(admin.ModelAdmin):
    list_display = ('rendicion', 'tipo_servicio', 'ingresos', 'egresos', 'beneficiario_real')
    list_filter = ('tipo_servicio', 'beneficiario_real')
    search_fields = ('rendicion__chofer__nombre',)


@admin.register(Chofer)
class ChoferAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'celular', 'vencimiento_licencia', 'licencia_estado')
    search_fields = ('nombre', 'email', 'celular')

    def licencia_estado(self, obj):
        hoy = date.today()
        if obj.vencimiento_licencia:
            if obj.vencimiento_licencia < hoy:
                return format_html('<span style="color: red; font-weight: bold;">VENCIDA</span>')
            elif obj.vencimiento_licencia <= hoy + timedelta(days=30):
                return format_html('<span style="color: orange; font-weight: bold;">PRONTO A VENCER</span>')
            else:
                return format_html('<span style="color: green;">Vigente</span>')
        return format_html('<span style="color: gray;">Sin fecha</span>')

    licencia_estado.short_description = 'Estado Licencia'

