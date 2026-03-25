"""
Punto de entrada — Análisis de Combinaciones - Lotería IA
Ejecutar con: python main.py
"""
import sys
import os

# Suprimir mensajes verbosos de TensorFlow antes de importar nada
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import logging
logging.getLogger("tensorflow").setLevel(logging.ERROR)

# Asegurar que el directorio del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _check_dependencies():
    missing = []
    for pkg in ["customtkinter", "numpy"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("=" * 60)
        print("DEPENDENCIAS FALTANTES")
        print("=" * 60)
        print(f"Paquetes no instalados: {', '.join(missing)}")
        print("\nInstala las dependencias ejecutando:")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    _check_dependencies()
    from gui.app import LotteryAnalyzerApp
    app = LotteryAnalyzerApp()
    app.run()
