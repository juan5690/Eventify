import subprocess
import sys
import time

if __name__ == "__main__":
    print("🚀 Iniciando Backend (FastAPI) en http://127.0.0.1:8000 ...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"]
    )
    
    time.sleep(2)
    
    print("📊 Iniciando Frontend (Streamlit)...")
    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py"]
    )

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
        backend.terminate()
        frontend.terminate()