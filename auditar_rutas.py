from app import app
for r in app.url_map.iter_rules():
    print(f'Ruta: {r.rule} --> Endpoint: {r.endpoint}')
