from django import template
from django.urls import resolve

register = template.Library()


@register.simple_tag(takes_context=True)
def selecciona_menu(context, *view_names):
    """
    Etiqueta de template que devuelve 'active' si la vista actual coincide
    con alguno de los nombres de vista proporcionados.
    
    Uso:
        {% selecciona_menu 'index' %}
        {% selecciona_menu 'services' 'goods_storage' 'air_freight_service' %}
    
    Args:
        context: El contexto del template (automático)
        *view_names: Uno o más nombres de vistas a comparar
    
    Returns:
        'active' si la vista actual coincide, cadena vacía en caso contrario
    """
    try:
        # Obtener la vista resuelta de la URL actual
        request = context.get('request')
        if not request:
            return ''
        
        # Resolver la URL actual para obtener el nombre de la vista
        resolver_match = resolve(request.path)
        current_view_name = resolver_match.view_name
        
        # Si el nombre de la vista incluye el namespace de la app (ej: 'website_app:index')
        # extraer solo el nombre de la vista
        if ':' in current_view_name:
            current_view_name = current_view_name.split(':')[1]
        
        # Comparar con los nombres de vista proporcionados
        if current_view_name in view_names:
            return 'active'
        
        return ''
    except Exception:
        # En caso de error, devolver cadena vacía
        return ''

