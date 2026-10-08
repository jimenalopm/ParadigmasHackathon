"""Punto de entrada de la Central de emergencias.

    python central_emergencias.py             -> interfaz gráfica (recomendado)
    python central_emergencias.py --consola   -> menú de texto

Archivos del sistema:
    nucleo.py            reglas y datos (paradigma funcional, sin interfaz)
    interfaz_grafica.py  ventana (tkinter)
    consola.py           menú de texto
"""
import sys


def main() -> None:
    if "--consola" in sys.argv:
        import consola
        consola.main()
        return
    try:
        import interfaz_grafica
    except ImportError:   # tkinter no está instalado en este Python
        print("No se encontró tkinter: se abre el menú de consola.")
        import consola
        consola.main()
        return
    interfaz_grafica.iniciar()


if __name__ == "__main__":
    main()
