import ast

def listar_modelos():
    try:
        with open('models.py', 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        print("\n🔍 Clases detectadas en models.py:")
        print("-" * 40)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                print(f"• {node.name}")
        print("-" * 40)
        print("Copia estos nombres y pégalos aquí para adaptar el generador de datos.")

    except FileNotFoundError:
        print("❌ No se encontró el archivo models.py en este directorio.")

if __name__ == '__main__':
    listar_modelos()