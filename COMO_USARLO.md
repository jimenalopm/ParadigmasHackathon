# Central de emergencias – Cómo usarlo

Sistema para registrar y atender emergencias en Villa Paradigma.
Versión principal: **funcional** (Python). Segunda versión: **lógico** (Prolog).

## Ejecutar (Python 3, no hay que instalar nada)

```
python central_emergencias.py             # interfaz gráfica (recomendado)
python central_emergencias.py --consola   # menú de texto
```

En Windows use `python` o `py` (en otros sistemas, `python3`).
Si Python no trae `tkinter`, el programa abre automáticamente el menú de consola.

## Interfaz gráfica

| Zona de la pantalla | Qué hace |
|---|---|
| **Nueva emergencia** (izquierda) | Elija tipo, zona y gravedad y presione *Registrar emergencia* |
| **Emergencias abiertas** (centro) | Lista de la más urgente a la menos urgente. Rojo = muy alta, ámbar = alta, verde = baja, gris = ya en atención |
| **Asignar unidad a la más grave** | Envía una unidad libre y compatible a la emergencia pendiente más urgente |
| **Cerrar seleccionada** | Seleccione una fila de la lista y ciérrela: su unidad queda libre |
| **Unidades** (derecha) | Qué unidades están libres u ocupadas, y qué tipos atiende cada una |
| **Resumen por zona** (abajo) | Pendientes y en atención por zona (borde rojo = hay pendientes) |
| **Medidor de capacidad** (arriba) | Emergencias abiertas / máximo. Pasa de verde a ámbar (70 %) y a rojo (lleno) |

Los mensajes aparecen en la barra inferior: verde ✔ si salió bien, rojo ✖ si no se pudo y por qué.

### Ejemplo rápido
1. Tipo `médica`, zona `Centro`, gravedad `muy alta` → *Registrar emergencia*
2. *Asignar unidad a la más grave* → "Ambulancia 1 asignada a la emergencia #1"
3. Seleccione la fila #1 → *Cerrar seleccionada* → la ambulancia queda libre

## Reglas
- **Los rescates en la Ribera van antes que cualquier otra emergencia** (Cambio 1).
- Se atiende primero la de mayor gravedad; si empatan, la que llegó primero.
- **Regla justa** (Cambio 2): por cada 3 emergencias nuevas que llegan mientras una sigue pendiente, esta sube un nivel de gravedad (hasta *muy alta*). En la lista se ve con una flecha (`ALTA ↑ · era baja`). La gravedad registrada no se borra.
- La **Lancha** solo hace rescates en la Ribera.
- Cada unidad atiende una sola emergencia a la vez.
- Si no hay unidad compatible libre, la emergencia sigue pendiente (el sistema lo avisa y atiende la siguiente que sí tenga unidad).
- Para un rescate se prefiere la unidad más especializada (la Patrulla).

| Unidad | Puede atender |
|---|---|
| Ambulancia 1 y 2 | médicas y rescates |
| Bomberos 1 y 2 | incendios y rescates |
| Patrulla de rescate | solo rescates |

## Validaciones
- Tipo, zona y gravedad deben ser opciones válidas (en consola no importan tildes ni mayúsculas: `MEDICA` = `médica`).
- No se puede cerrar una emergencia que no existe o que aún no tiene unidad.
- Los nombres nuevos no pueden estar vacíos, repetidos ni pasar de 30 caracteres.
- Un error nunca cambia el estado del sistema: solo muestra el mensaje.

## Cuando se llena el tope (por defecto 10 emergencias abiertas)
Se elige en *Ajustes del sistema → Si se llena el tope*:
- **Rechazar nuevas**: no entran más emergencias hasta cerrar alguna.
- **Reemplazar la menos grave**: una emergencia **más grave** que la menos urgente de las pendientes la desplaza (el sistema avisa cuál salió). Si todas están en atención o no es más grave, se rechaza.

*Cambiar capacidad…* sube o baja el máximo (1 a 999) sin tocar el código.

## Crecer sin tocar el código (Ajustes del sistema)
- **+ Tipo**: nueva categoría (por ejemplo `inundación`). Si ninguna unidad la atiende, aparece el aviso amarillo "Sin unidad para: …".
- **+ Unidad**: nueva unidad (por ejemplo `Lancha 1`) y los tipos que atiende.
- **+ Zona**: nueva zona de la ciudad. Las tarjetas se acomodan solas.

## Archivos
| Archivo | Contenido |
|---|---|
| `central_emergencias.py` | Punto de entrada |
| `nucleo.py` | Reglas y datos (paradigma funcional, sin interfaz) |
| `interfaz_grafica.py` | Ventana (tkinter) |
| `consola.py` | Menú de texto |
| `emergencias.pl` | Segunda versión en Prolog |

## Segunda versión: Prolog (`emergencias.pl`)

Necesita SWI-Prolog. Para probarla:

```
swipl emergencias.pl
```

```
?- unidad_para(emergencia(1, rescate, sur, alta), Unidad).
?- assertz(ocupada(patrulla_rescate)).
?- puede_atender(bomberos_1, emergencia(2, incendio, norte, alta)).
```

## Decisiones donde la tarjeta no era clara
- El tope cuenta emergencias **abiertas** (al cerrar una se libera espacio).
- Si la más grave no tiene unidad compatible libre, se asigna la siguiente más grave que sí tenga.
- No se puede cerrar una emergencia que todavía no tiene unidad.
