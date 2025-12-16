# check_routes_fixed.py
from app import app

def check_routes():
    print("=== RUTAS REGISTRADAS ===")
    routes = []
    
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        routes.append((rule.endpoint, methods, rule.rule))
    
    # Ordenar por endpoint para mejor visualización
    routes.sort(key=lambda x: x[0])
    
    for endpoint, methods, rule in routes:
        print(f"{endpoint:50} {methods:20} {rule}")
    
    print(f"\n📊 Total de rutas: {len(routes)}")
    
    # Agrupar por blueprint
    print("\n=== RUTAS POR BLUEPRINT ===")
    blueprints = {}
    for endpoint, methods, rule in routes:
        if '.' in endpoint:
            blueprint_name = endpoint.split('.')[0]
            if blueprint_name not in blueprints:
                blueprints[blueprint_name] = []
            blueprints[blueprint_name].append((endpoint, methods, rule))
        else:
            if 'main' not in blueprints:
                blueprints['main'] = []
            blueprints['main'].append((endpoint, methods, rule))
    
    for blueprint, bp_routes in blueprints.items():
        print(f"\n🔷 {blueprint.upper()} ({len(bp_routes)} rutas):")
        for endpoint, methods, rule in bp_routes:
            print(f"   {endpoint:45} {methods:15} {rule}")

if __name__ == '__main__':
    check_routes()