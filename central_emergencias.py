"""Central de emergencias - Villa Paradigma (versión FUNCIONAL).

Idea del paradigma funcional:
  * Los datos son INMUTABLES (tuplas y dataclasses "frozen").
  * Cada operación es una FUNCIÓN que recibe el estado y DEVUELVE un estado nuevo.
  * Se usan map, filter, sorted/min y reduce en lugar de modificar listas.
Solo la función `main` (el menú) habla con el usuario; todo lo demás es puro.
"""
from dataclasses import dataclass, replace
from functools import reduce
from typing import Optional, Tuple

ZONAS = ("Centro", "Ribera", "Norte", "Sur", "Este", "Oeste")
TIPOS = ("medica", "incendio", "rescate")
PESO_GRAVEDAD = {"baja": 1, "alta": 2, "muy alta": 3}
MAX_EMERGENCIAS = 10


@dataclass(frozen=True)
class Unidad:
    nombre: str
    atiende: Tuple[str, ...]
    ocupada: bool = False


@dataclass(frozen=True)
class Emergencia:
    id: int  # el número crece con la llegada: sirve para desempatar
    tipo: str
    zona: str
    gravedad: str
    unidad: Optional[str] = None  # None = pendiente; con nombre = en atención


@dataclass(frozen=True)
class Estado:
    emergencias: Tuple[Emergencia, ...]
    unidades: Tuple[Unidad, ...]
    siguiente_id: int = 1


UNIDADES_INICIALES = (
    Unidad("Ambulancia 1", ("medica", "rescate")),
    Unidad("Ambulancia 2", ("medica", "rescate")),
    Unidad("Bomberos 1", ("incendio", "rescate")),
    Unidad("Bomberos 2", ("incendio", "rescate")),
    Unidad("Patrulla de rescate", ("rescate",)),
)


def estado_inicial() -> Estado:
    return Estado(emergencias=(), unidades=UNIDADES_INICIALES)


# ---------- Funciones puras de consulta ----------

def prioridad(e: Emergencia) -> Tuple[int, int]:
    """Clave de orden: mayor gravedad primero; si empatan, la que llegó antes."""
    return (-PESO_GRAVEDAD[e.gravedad], e.id)


def pendientes(estado: Estado) -> Tuple[Emergencia, ...]:
    """Emergencias sin unidad, de la más grave a la menos grave."""
    sin_unidad = filter(lambda e: e.unidad is None, estado.emergencias)
    return tuple(sorted(sin_unidad, key=prioridad))


def unidades_libres_para(estado: Estado, e: Emergencia) -> Tuple[Unidad, ...]:
    return tuple(filter(lambda u: not u.ocupada and e.tipo in u.atiende,
                        estado.unidades))


def elegir_unidad(libres: Tuple[Unidad, ...]) -> Unidad:
    """Entre las compatibles se usa la más especializada (la que atiende
    menos tipos), para no gastar una ambulancia en un rescate si hay patrulla."""
    return min(libres, key=lambda u: len(u.atiende))


def resumen_por_zona(estado: Estado) -> Tuple[Tuple[str, int, int], ...]:
    """Por cada zona: (zona, pendientes, en atención)."""
    def contar(zona):
        de_zona = tuple(filter(lambda e: e.zona == zona, estado.emergencias))
        pend = len(tuple(filter(lambda e: e.unidad is None, de_zona)))
        return (zona, pend, len(de_zona) - pend)
    return tuple(map(contar, ZONAS))


# ---------- Operaciones: devuelven (estado_nuevo, mensaje) ----------

def registrar(estado: Estado, tipo: str, zona: str, gravedad: str):
    if len(estado.emergencias) >= MAX_EMERGENCIAS:
        return estado, f"No se puede: ya hay {MAX_EMERGENCIAS} emergencias abiertas."
    if tipo not in TIPOS:
        return estado, f"Tipo inválido. Opciones: {', '.join(TIPOS)}."
    if zona not in ZONAS:
        return estado, f"Zona inválida. Opciones: {', '.join(ZONAS)}."
    if gravedad not in PESO_GRAVEDAD:
        return estado, "Gravedad inválida. Opciones: baja, alta, muy alta."
    nueva = Emergencia(estado.siguiente_id, tipo, zona, gravedad)
    nuevo = replace(estado,
                    emergencias=estado.emergencias + (nueva,),
                    siguiente_id=estado.siguiente_id + 1)
    return nuevo, f"Emergencia #{nueva.id} registrada ({tipo}, {zona}, {gravedad})."


def asignar(estado: Estado):
    """Asigna una unidad a la emergencia pendiente más grave que TENGA una
    unidad compatible libre. Las que no tengan unidad siguen pendientes."""
    candidatas = tuple(filter(lambda e: unidades_libres_para(estado, e),
                              pendientes(estado)))
    if not pendientes(estado):
        return estado, "No hay emergencias pendientes."
    if not candidatas:
        return estado, "No hay unidad compatible libre: las emergencias siguen pendientes."
    e = candidatas[0]
    u = elegir_unidad(unidades_libres_para(estado, e))
    nuevo = replace(
        estado,
        emergencias=tuple(map(lambda x: replace(x, unidad=u.nombre) if x.id == e.id else x,
                              estado.emergencias)),
        unidades=tuple(map(lambda x: replace(x, ocupada=True) if x.nombre == u.nombre else x,
                           estado.unidades)),
    )
    return nuevo, f"{u.nombre} asignada a la emergencia #{e.id} ({e.tipo}, {e.zona}, {e.gravedad})."


def cerrar(estado: Estado, id_emergencia: int):
    e = next(filter(lambda x: x.id == id_emergencia, estado.emergencias), None)
    if e is None:
        return estado, f"No existe la emergencia #{id_emergencia}."
    if e.unidad is None:
        return estado, f"La emergencia #{id_emergencia} aún no tiene unidad: no se puede cerrar."
    nuevo = replace(
        estado,
        emergencias=tuple(filter(lambda x: x.id != id_emergencia, estado.emergencias)),
        unidades=tuple(map(lambda u: replace(u, ocupada=False) if u.nombre == e.unidad else u,
                           estado.unidades)),
    )
    return nuevo, f"Emergencia #{id_emergencia} cerrada. {e.unidad} quedó libre."


# ---------- Presentación (texto) ----------

def texto_pendientes(estado: Estado) -> str:
    pend = pendientes(estado)
    if not pend:
        return "No hay emergencias pendientes."
    lineas = map(lambda e: f"  #{e.id}  {e.gravedad:<8} {e.tipo:<8} {e.zona}", pend)
    return "Pendientes (de la más grave a la menos grave):\n" + "\n".join(lineas)


def texto_atencion(estado: Estado) -> str:
    en_atencion = tuple(filter(lambda e: e.unidad is not None, estado.emergencias))
    if not en_atencion:
        return ""
    lineas = map(lambda e: f"  #{e.id}  {e.tipo:<8} {e.zona:<7} -> {e.unidad}", en_atencion)
    return "En atención:\n" + "\n".join(lineas)


def texto_resumen(estado: Estado) -> str:
    filas = map(lambda r: f"  {r[0]:<7} pendientes: {r[1]}   en atención: {r[2]}",
                resumen_por_zona(estado))
    total = reduce(lambda acc, r: acc + r[1] + r[2], resumen_por_zona(estado), 0)
    return "Emergencias por zona:\n" + "\n".join(filas) + f"\n  Total abiertas: {total}"


MENU = """
=== CENTRAL DE EMERGENCIAS ===
1. Registrar emergencia
2. Ver pendientes
3. Asignar unidad
4. Cerrar emergencia
5. Resumen por zona
0. Salir"""


def pedir_opcion(texto: str, opciones) -> str:
    return input(f"{texto} ({'/'.join(opciones)}): ").strip().lower()


def main() -> None:
    estado = estado_inicial()
    while True:
        print(MENU)
        op = input("Opción: ").strip()
        if op == "1":
            tipo = pedir_opcion("Tipo", TIPOS)
            zona = pedir_opcion("Zona", ZONAS).capitalize()
            gravedad = pedir_opcion("Gravedad", PESO_GRAVEDAD)
            estado, msg = registrar(estado, tipo, zona, gravedad)
            print(msg)
        elif op == "2":
            print(texto_pendientes(estado))
            print(texto_atencion(estado))
        elif op == "3":
            estado, msg = asignar(estado)
            print(msg)
        elif op == "4":
            dato = input("Número de la emergencia a cerrar: ").strip()
            if dato.isdigit():
                estado, msg = cerrar(estado, int(dato))
            else:
                msg = "Escriba un número válido."
            print(msg)
        elif op == "5":
            print(texto_resumen(estado))
        elif op == "0":
            print("Hasta pronto.")
            break
        else:
            print("Opción no válida. Use un número del menú.")


if __name__ == "__main__":
    main()
