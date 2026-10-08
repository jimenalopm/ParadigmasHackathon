# Central de emergencias – Cómo usarlo

Sistema para registrar y atender emergencias en Villa Paradigma.
Versión principal: **funcional** (Python). Segunda versión: **lógico** (Prolog).

## Versión funcional (Python 3)

Solo necesita Python 3.8 o más nuevo. No hay que instalar nada.

```
python3 central_emergencias.py
```

Aparece este menú; escriba el número y presione Enter:

```
=== CENTRAL DE EMERGENCIAS ===
1. Registrar emergencia
2. Ver pendientes
3. Asignar unidad
4. Cerrar emergencia
5. Resumen por zona
0. Salir
```

| Opción | Qué hace | Qué le pide |
|---|---|---|
| 1 | Registra una emergencia (máximo 10 abiertas) | Tipo: `medica`, `incendio` o `rescate`; zona: `Centro`, `Ribera`, `Norte`, `Sur`, `Este` u `Oeste`; gravedad: `baja`, `alta` o `muy alta` |
| 2 | Muestra las pendientes de la más grave a la menos grave, y las que están en atención | Nada |
| 3 | Asigna una unidad libre y compatible a la emergencia pendiente más grave (si empatan, la que llegó primero) | Nada |
| 4 | Cierra una emergencia atendida y deja libre su unidad | El número de la emergencia (el `#` que muestra el sistema) |
| 5 | Muestra cuántas emergencias hay por zona (pendientes y en atención) | Nada |

### Ejemplo rápido

1. Opción `1` → `medica` → `Centro` → `muy alta`
2. Opción `3` → "Ambulancia 1 asignada a la emergencia #1"
3. Opción `4` → `1` → la emergencia se cierra y la ambulancia queda libre

### Reglas importantes

- Se atiende primero la de mayor gravedad; si empatan, la que llegó primero.
- Cada unidad atiende una sola emergencia a la vez.
- Si no hay unidad compatible libre, la emergencia sigue pendiente (el sistema lo avisa).
- Si escribe algo inválido (tipo, zona, número…), el sistema muestra un mensaje y no cambia nada.

| Unidad | Puede atender |
|---|---|
| Ambulancia 1 y 2 | médicas y rescates |
| Bomberos 1 y 2 | incendios y rescates |
| Patrulla de rescate | solo rescates |

## Segunda versión: Prolog (`emergencias.pl`)

Necesita SWI-Prolog. Para probarla:

```
swipl emergencias.pl
```

Ejemplos de consultas:

```
?- unidad_para(emergencia(1, rescate, sur, alta), Unidad).
?- assertz(ocupada(patrulla_rescate)).
?- puede_atender(bomberos_1, emergencia(2, incendio, norte, alta)).
```

## Decisiones que tomamos donde la tarjeta no era clara

- El tope de 10 cuenta emergencias **abiertas** (al cerrar una se libera espacio).
- Si la más grave no tiene unidad compatible libre, se asigna la siguiente más grave que sí tenga.
- Para un rescate se prefiere la unidad más especializada (la Patrulla) antes que una ambulancia o bomberos.
- No se puede cerrar una emergencia que todavía no tiene unidad.
