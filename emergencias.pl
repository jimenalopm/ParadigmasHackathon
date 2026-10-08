% Central de emergencias - SEGUNDA VERSION (logico, Prolog)
% Regla principal: que unidad puede atender cada tipo de emergencia.

% Unidades ocupadas (se agregan con assertz al asignar).
:- dynamic ocupada/1.

% Hechos: que tipos atiende cada unidad.
atiende(ambulancia_1, medica).
atiende(ambulancia_1, rescate).
atiende(ambulancia_2, medica).
atiende(ambulancia_2, rescate).
atiende(bomberos_1, incendio).
atiende(bomberos_1, rescate).
atiende(bomberos_2, incendio).
atiende(bomberos_2, rescate).
atiende(patrulla_rescate, rescate).

% Regla: una unidad puede atender una emergencia si atiende ese tipo.
puede_atender(Unidad, emergencia(_, Tipo, _, _)) :- atiende(Unidad, Tipo).

% Regla: unidades que la pueden atender y estan libres.
unidad_para(Emergencia, Unidad) :-
    puede_atender(Unidad, Emergencia),
    \+ ocupada(Unidad).
