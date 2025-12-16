from app import app
import os
import re

def check_broken_links():
    # Obtener todos los endpoints registrados
    registered_endpoints = set()
    for rule in app.url_map.iter_rules():
        registered_endpoints.add(rule.endpoint)
    
    print("Endpoints registrados:", len(registered_endpoints))
    
    # Buscar en todas las plantillas
    templates_dir = 'templates'
    broken_links = []
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Buscar todas las llamadas a url_for
                url_for_pattern = r"url_for\('([^']+)'\)"
                matches = re.findall(url_for_pattern, content)
                
                for endpoint in matches:
                    if endpoint not in registered_endpoints:
                        broken_links.append({
                            'file': filepath,
                            'endpoint': endpoint,
                            'suggestions': find_similar_endpoints(endpoint, registered_endpoints)
                        })
    
    # Mostrar resultados
    if broken_links:
        print("\n❌ ENLACES ROTOS ENCONTRADOS:")
        for link in broken_links:
            print(f"\nArchivo: {link['file']}")
            print(f"Endpoint no encontrado: '{link['endpoint']}'")
            if link['suggestions']:
                print(f"Sugerencias: {', '.join(link['suggestions'])}")
    else:
        print("\n✅ No se encontraron enlaces rotos")

def find_similar_endpoints(broken_endpoint, registered_endpoints):
    suggestions = []
    for endpoint in registered_endpoints:
        if broken_endpoint.split('.')[-1] in endpoint:
            suggestions.append(endpoint)
    return suggestions[:3]  # Máximo 3 sugerencias

if __name__ == '__main__':
    check_broken_links()