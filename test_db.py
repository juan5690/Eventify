from backend.database import get_db

db = get_db()
try:
    colecciones = db.list_collection_names()
    print("✅ Conexión exitosa a MongoDB.")
    print("Colecciones encontradas:", colecciones)
    for col in ["usuarios", "eventos", "ordenes_compra", "resenas_evaluaciones"]:
        print(f" - {col}: {db[col].count_documents({})} documentos")
except Exception as e:
    print("❌ Error de conexión:", e)