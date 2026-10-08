"""Núcleo de la Central de emergencias de Villa Paradigma (paradigma FUNCIONAL).

Este archivo NO sabe nada de ventanas ni de consola: solo contiene los datos y
las reglas. Así la interfaz gráfica y el menú de consola usan exactamente la
misma lógica.

Ideas del paradigma funcional que se usan aquí:
  * Datos INMUTABLES: dataclasses "frozen" y tuplas. Nada se modifica en su lugar.
  * Funciones PURAS: cada operación recibe un `Estado` y devuelve un `Resultado`
    que trae un estado NUEVO (el original queda intacto).
  * Comprensiones, min/sorted y Counter en lugar de ciclos que cambian listas.

Escalabilidad: las categorías (tipos, zonas, gravedades), las unidades, la
capacidad y la política cuando se llena el tope viven DENTRO del `Estado`.
Agregar un tipo, una zona o una unidad es solo una operación más.
"""
import unicodedata
from collections import Counter
from dataclasses import dataclass, replace
from typing import Optional, Tuple

# ---------------------------------------------------------------- Constantes
MAX_NOMBRE = 30          # largo máximo de nombres de unidades, tipos y zonas
CAPACIDAD_MAXIMA = 999   # límite razonable para la capacidad configurable
POLITICAS = ("rechazar", "reemplazar")  # qué hacer cuando se llena el tope


# ------------------------------------------------------------------- Datos
@dataclass(frozen=True)
class Unidad:
    nombre: str
    atiende: Tuple[str, ...]   # tipos de emergencia que puede atender
    ocupada: bool = False


@dataclass(frozen=True)
class Emergencia:
    id: int                    # crece con la llegada: sirve para desempatar
    tipo: str
    zona: str
    gravedad: str
    unidad: Optional[str] = None  # None = pendiente; con nombre = en atención


@dataclass(frozen=True)
class Estado:
    """Todo lo que el sistema 'sabe' en un momento dado."""
    emergencias: Tuple[Emergencia, ...] = ()   # solo las ABIERTAS
    unidades: Tuple[Unidad, ...] = ()
    tipos: Tuple[str, ...] = ()
    zonas: Tuple[str, ...] = ()
    gravedades: Tuple[str, ...] = ()           # ordenadas de MENOR a MAYOR
    capacidad: int = 10                        # máximo de emergencias abiertas
    politica_tope: str = "rechazar"            # ver POLITICAS
    siguiente_id: int = 1


@dataclass(frozen=True)
class Resultado:
    """Lo que devuelve toda operación: estado nuevo + mensaje + si salió bien."""
    estado: Estado
    mensaje: str
    ok: bool = True


def _es_entero(valor) -> bool:
    """True solo para enteros de verdad (en Python, True/False también son int)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def _fallo(estado: Estado, mensaje: str) -> Resultado:
    """Operación rechazada: el estado NO cambia."""
    return Resultado(estado, mensaje, ok=False)


def estado_inicial() -> Estado:
    """Datos iniciales de la tarjeta (escritos en el código, sin base de datos)."""
    return Estado(
        unidades=(
            Unidad("Ambulancia 1", ("médica", "rescate")),
            Unidad("Ambulancia 2", ("médica", "rescate")),
            Unidad("Bomberos 1", ("incendio", "rescate")),
            Unidad("Bomberos 2", ("incendio", "rescate")),
            Unidad("Patrulla de rescate", ("rescate",)),
        ),
        tipos=("médica", "incendio", "rescate"),
        zonas=("Centro", "Ribera", "Norte", "Sur", "Este", "Oeste"),
        gravedades=("baja", "alta", "muy alta"),
    )


# ------------------------------------------------- Normalización y búsqueda
def clave(texto) -> str:
    """Forma comparable de un texto: sin tildes, sin mayúsculas, sin espacios
    de más. Así 'MÉDICA ', 'medica' y 'Médica' se consideran iguales."""
    sin_tildes = unicodedata.normalize("NFD", str(texto))
    sin_marcas = "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")
    return " ".join(sin_marcas.lower().split())


def buscar(valor, opciones) -> Optional[str]:
    """Devuelve la opción oficial que coincide con `valor`, o None."""
    k = clave(valor)
    return next((o for o in opciones if clave(o) == k), None)


def _nombre_valido(nombre, existentes) -> Tuple[str, Optional[str]]:
    """Valida un nombre nuevo. Devuelve (nombre_limpio, mensaje_de_error|None)."""
    limpio = " ".join(str(nombre).split())
    if not limpio:
        return limpio, "El nombre no puede estar vacío."
    if len(limpio) > MAX_NOMBRE:
        return limpio, f"El nombre es muy largo (máximo {MAX_NOMBRE} caracteres)."
    if buscar(limpio, existentes):
        return limpio, f"'{limpio}' ya existe."
    return limpio, None


# ------------------------------------------------------ Consultas (puras)
def peso(estado: Estado, gravedad: str) -> int:
    """Número de la gravedad: más alto = más grave."""
    return estado.gravedades.index(gravedad)


def prioridad(estado: Estado, e: Emergencia) -> Tuple[int, int]:
    """Clave de orden: el MENOR valor es el más urgente.
    Mayor gravedad primero; si empatan, la que llegó antes (id menor)."""
    return (-peso(estado, e.gravedad), e.id)


def pendientes(estado: Estado) -> Tuple[Emergencia, ...]:
    """Emergencias sin unidad, de la más grave a la menos grave."""
    sin_unidad = (e for e in estado.emergencias if e.unidad is None)
    return tuple(sorted(sin_unidad, key=lambda e: prioridad(estado, e)))


def en_atencion(estado: Estado) -> Tuple[Emergencia, ...]:
    return tuple(e for e in estado.emergencias if e.unidad is not None)


def unidades_libres_para(estado: Estado, e: Emergencia) -> Tuple[Unidad, ...]:
    """Unidades libres que SÍ pueden atender el tipo de esta emergencia."""
    return tuple(u for u in estado.unidades if not u.ocupada and e.tipo in u.atiende)


def elegir_unidad(libres: Tuple[Unidad, ...]) -> Unidad:
    """Entre las compatibles, la más especializada (la que atiende menos
    tipos), para no gastar una ambulancia en un rescate si hay patrulla."""
    return min(libres, key=lambda u: len(u.atiende))


def resumen_por_zona(estado: Estado) -> Tuple[Tuple[str, int, int], ...]:
    """Por cada zona: (zona, pendientes, en atención). Una sola pasada."""
    pend = Counter(e.zona for e in estado.emergencias if e.unidad is None)
    aten = Counter(e.zona for e in estado.emergencias if e.unidad is not None)
    return tuple((z, pend[z], aten[z]) for z in estado.zonas)


def tipos_sin_cobertura(estado: Estado) -> Tuple[str, ...]:
    """Tipos de emergencia que NINGUNA unidad puede atender (aviso de diseño)."""
    cubiertos = {t for u in estado.unidades for t in u.atiende}
    return tuple(t for t in estado.tipos if t not in cubiertos)


# ------------------------------------------------- Operaciones del menú
def registrar(estado: Estado, tipo, zona, gravedad) -> Resultado:
    """Registra una emergencia. Valida los datos y maneja el tope de capacidad."""
    t = buscar(tipo, estado.tipos)
    z = buscar(zona, estado.zonas)
    g = buscar(gravedad, estado.gravedades)
    if t is None:
        return _fallo(estado, f"Tipo inválido. Opciones: {', '.join(estado.tipos)}.")
    if z is None:
        return _fallo(estado, f"Zona inválida. Opciones: {', '.join(estado.zonas)}.")
    if g is None:
        return _fallo(estado, f"Gravedad inválida. Opciones: {', '.join(estado.gravedades)}.")

    nueva = Emergencia(estado.siguiente_id, t, z, g)
    base, aviso = estado, ""

    if len(estado.emergencias) >= estado.capacidad:
        # --- Tope alcanzado: se aplica la política configurada ---
        desplazable = _menos_urgente_pendiente(estado)
        puede_reemplazar = (
            estado.politica_tope == "reemplazar"
            and desplazable is not None
            and peso(estado, g) > peso(estado, desplazable.gravedad)
        )
        if not puede_reemplazar:
            return _fallo(estado, f"Capacidad llena ({estado.capacidad} emergencias abiertas). "
                                  "Cierre alguna o suba la capacidad.")
        base = replace(estado, emergencias=tuple(e for e in estado.emergencias
                                                 if e.id != desplazable.id))
        aviso = (f" Capacidad llena: se desplazó la #{desplazable.id} "
                 f"({desplazable.gravedad}) por ser la menos urgente.")

    nuevo = replace(base, emergencias=base.emergencias + (nueva,),
                    siguiente_id=base.siguiente_id + 1)
    return Resultado(nuevo, f"Emergencia #{nueva.id} registrada ({t}, {z}, {g}).{aviso}")


def _menos_urgente_pendiente(estado: Estado) -> Optional[Emergencia]:
    """La pendiente de menor prioridad (candidata a ser desplazada)."""
    pend = pendientes(estado)
    return pend[-1] if pend else None   # `pendientes` ya viene ordenada


def asignar(estado: Estado) -> Resultado:
    """Asigna una unidad libre y compatible a la pendiente más grave que TENGA
    una unidad disponible. Las demás siguen pendientes."""
    pend = pendientes(estado)
    if not pend:
        return _fallo(estado, "No hay emergencias pendientes.")
    for e in pend:                                  # ya vienen en orden de urgencia
        libres = unidades_libres_para(estado, e)
        if libres:
            u = elegir_unidad(libres)
            nuevo = replace(
                estado,
                emergencias=tuple(replace(x, unidad=u.nombre) if x.id == e.id else x
                                  for x in estado.emergencias),
                unidades=tuple(replace(x, ocupada=True) if x.nombre == u.nombre else x
                               for x in estado.unidades))
            return Resultado(nuevo, f"{u.nombre} asignada a la emergencia #{e.id} "
                                    f"({e.tipo}, {e.zona}, {e.gravedad}).")
    return _fallo(estado, "No hay unidad compatible libre: las emergencias siguen pendientes.")


def cerrar(estado: Estado, id_emergencia) -> Resultado:
    """Cierra una emergencia atendida y deja libre su unidad."""
    if not _es_entero(id_emergencia):
        return _fallo(estado, "El número de emergencia debe ser un entero.")
    e = next((x for x in estado.emergencias if x.id == id_emergencia), None)
    if e is None:
        return _fallo(estado, f"No existe la emergencia #{id_emergencia}.")
    if e.unidad is None:
        return _fallo(estado, f"La #{id_emergencia} aún no tiene unidad: asígnela antes de cerrarla.")
    nuevo = replace(
        estado,
        emergencias=tuple(x for x in estado.emergencias if x.id != id_emergencia),
        unidades=tuple(replace(u, ocupada=False) if u.nombre == e.unidad else u
                       for u in estado.unidades))
    return Resultado(nuevo, f"Emergencia #{id_emergencia} cerrada. {e.unidad} quedó libre.")


# --------------------------------------- Operaciones de escalabilidad/ajustes
def agregar_unidad(estado: Estado, nombre, tipos) -> Resultado:
    """Suma una unidad nueva (p. ej. un refuerzo durante la tormenta)."""
    limpio, error = _nombre_valido(nombre, [u.nombre for u in estado.unidades])
    if error:
        return _fallo(estado, error)
    oficiales = tuple(dict.fromkeys(buscar(t, estado.tipos) for t in tipos))  # sin repetidos
    if not oficiales or None in oficiales:
        return _fallo(estado, "Elija al menos un tipo de emergencia válido.")
    nuevo = replace(estado, unidades=estado.unidades + (Unidad(limpio, oficiales),))
    return Resultado(nuevo, f"Unidad '{limpio}' agregada ({', '.join(oficiales)}).")


def agregar_tipo(estado: Estado, nombre) -> Resultado:
    """Suma una categoría de emergencia (p. ej. 'inundación')."""
    limpio, error = _nombre_valido(nombre, estado.tipos)
    if error:
        return _fallo(estado, error)
    nuevo = replace(estado, tipos=estado.tipos + (limpio.lower(),))
    aviso = " Aún ninguna unidad la atiende: agregue una unidad." \
        if limpio.lower() in tipos_sin_cobertura(nuevo) else ""
    return Resultado(nuevo, f"Tipo '{limpio.lower()}' agregado.{aviso}")


def agregar_zona(estado: Estado, nombre) -> Resultado:
    """Suma una zona nueva a la ciudad."""
    limpio, error = _nombre_valido(nombre, estado.zonas)
    if error:
        return _fallo(estado, error)
    limpio = limpio[0].upper() + limpio[1:]
    return Resultado(replace(estado, zonas=estado.zonas + (limpio,)), f"Zona '{limpio}' agregada.")


def cambiar_capacidad(estado: Estado, capacidad) -> Resultado:
    """Cambia el máximo de emergencias abiertas. Si se baja por debajo de las
    abiertas actuales no se borra nada: solo se bloquean registros nuevos."""
    if not _es_entero(capacidad) or not 1 <= capacidad <= CAPACIDAD_MAXIMA:
        return _fallo(estado, f"La capacidad debe ser un entero entre 1 y {CAPACIDAD_MAXIMA}.")
    return Resultado(replace(estado, capacidad=capacidad), f"Capacidad cambiada a {capacidad}.")


def cambiar_politica(estado: Estado, politica) -> Resultado:
    """Elige qué pasa al llenarse el tope: 'rechazar' o 'reemplazar'."""
    if politica not in POLITICAS:
        return _fallo(estado, f"Política inválida. Opciones: {', '.join(POLITICAS)}.")
    return Resultado(replace(estado, politica_tope=politica), f"Si se llena el tope: {politica}.")
