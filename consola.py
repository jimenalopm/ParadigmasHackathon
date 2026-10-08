"""Menú de consola de la Central de emergencias.

Es la versión de texto del sistema. Sirve como respaldo si la interfaz gráfica
no está disponible. Usa exactamente la misma lógica de `nucleo.py`.
"""
import nucleo as n

MENU = """
=== CENTRAL DE EMERGENCIAS ===
1. Registrar emergencia
2. Ver pendientes
3. Asignar unidad
4. Cerrar emergencia
5. Resumen por zona
0. Salir"""


def texto_pendientes(estado: n.Estado) -> str:
    pend = n.pendientes(estado)
    lineas = ["Pendientes (de la más urgente a la menos urgente):"] if pend else ["No hay emergencias pendientes."]
    lineas += [f"  #{e.id}  {e.gravedad:<9} {e.tipo:<9} {e.zona}" for e in pend]
    atencion = n.en_atencion(estado)
    if atencion:
        lineas.append("En atención:")
        lineas += [f"  #{e.id}  {e.tipo:<9} {e.zona:<7} -> {e.unidad}" for e in atencion]
    return "\n".join(lineas)


def texto_resumen(estado: n.Estado) -> str:
    filas = n.resumen_por_zona(estado)
    lineas = [f"  {z:<8} pendientes: {p}   en atención: {a}" for z, p, a in filas]
    total = sum(p + a for _, p, a in filas)
    return "\n".join(["Emergencias por zona:", *lineas,
                      f"  Total abiertas: {total} de {estado.capacidad}"])


def pedir(texto: str, opciones) -> str:
    return input(f"{texto} ({'/'.join(opciones)}): ").strip()


def main() -> None:
    estado = n.estado_inicial()
    while True:
        print(MENU)
        opcion = input("Opción: ").strip()
        if opcion == "0":
            print("Hasta pronto.")
            return
        if opcion == "1":
            resultado = n.registrar(estado, pedir("Tipo", estado.tipos),
                                    pedir("Zona", estado.zonas),
                                    pedir("Gravedad", estado.gravedades))
        elif opcion == "2":
            print(texto_pendientes(estado))
            continue
        elif opcion == "3":
            resultado = n.asignar(estado)
        elif opcion == "4":
            dato = input("Número de la emergencia a cerrar: ").strip()
            # Si no es un número válido se pasa tal cual: el núcleo lo rechaza con un mensaje
            resultado = n.cerrar(estado, int(dato) if dato.isdigit() else dato)
        elif opcion == "5":
            print(texto_resumen(estado))
            continue
        else:
            print("Opción no válida. Use un número del menú.")
            continue
        estado = resultado.estado          # el estado nuevo reemplaza al anterior
        print(resultado.mensaje)


if __name__ == "__main__":
    main()
