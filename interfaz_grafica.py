"""Interfaz gráfica de la Central de emergencias (solo usa tkinter, ya incluido
con Python: no hay que instalar nada).

Esta capa SOLO dibuja y reacciona a los botones. Todas las reglas viven en
`nucleo.py`. El patrón es siempre el mismo:

    resultado = nucleo.operacion(self.estado, ...)   # función pura
    self._aplicar(resultado)                          # guarda el estado y redibuja

Así la pantalla nunca puede quedar distinta del estado real del sistema.
"""
import tkinter as tk
from tkinter import ttk, simpledialog
from tkinter import font as tkfont

import nucleo as n

# ----------------------------------------------------------------- Estilo
FONDO, PANEL, PANEL2, BORDE = "#0f1b2d", "#16263d", "#1d3350", "#2a4468"
TEXTO, SUAVE = "#e8eef7", "#8fa3bf"
ROJO, AMBAR, VERDE, AZUL = "#e5484d", "#f5a524", "#2fb67c", "#3b82f6"
FUENTE = "Segoe UI"   # si no existe (Linux/Mac), Tk usa una fuente parecida

ETIQUETAS_POLITICA = {"rechazar": "Rechazar nuevas",
                      "reemplazar": "Reemplazar la menos grave"}
ZONAS_POR_FILA = 8    # cuántas tarjetas de zona caben en una fila


def _mezclar(color: str, con: int, f: float) -> str:
    """Mezcla un color '#rrggbb' con blanco (con=255) o negro (con=0)."""
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(int(c + (con - c) * f) for c in (r, g, b))


def _aclarar(color: str, f: float = 0.18) -> str:
    return _mezclar(color, 255, f)


def _oscurecer(color: str, f: float = 0.35) -> str:
    return _mezclar(color, 0, f)


def _rect_redondeado(lienzo, x1, y1, x2, y2, r, **opts):
    """Rectángulo con esquinas redondeadas (polígono suavizado)."""
    puntos = (x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
              x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1)
    return lienzo.create_polygon(puntos, smooth=True, **opts)


class _BotonRedondeado(tk.Canvas):
    """Botón con esquinas redondeadas, sombra, efecto al pasar el mouse y al
    presionar. Se dibuja en un Canvas porque tk.Button no permite bordes redondos."""
    SOMBRA, RADIO = 3, 9

    def __init__(self, parent, texto, comando, color, padx=12, pady=8,
                 font=(FUENTE, 10, "bold"), fg="white"):
        fuente = tkfont.Font(font=font)
        alto = fuente.metrics("linespace") + 2 * pady + self.SOMBRA
        super().__init__(parent, width=fuente.measure(texto) + 2 * padx, height=alto,
                         bg=parent.cget("bg"), highlightthickness=0, bd=0, cursor="hand2")
        self.texto, self.comando, self.color = texto, comando, color
        self.fuente, self.fg = fuente, fg
        self.encima = self.presionado = False
        self.bind("<Configure>", lambda _e: self._dibujar())
        self.bind("<Enter>", lambda _e: self._estado(encima=True))
        self.bind("<Leave>", lambda _e: self._estado(encima=False, presionado=False))
        self.bind("<ButtonPress-1>", lambda _e: self._estado(presionado=True))
        self.bind("<ButtonRelease-1>", self._soltar)

    def _estado(self, **cambios):
        for k, v in cambios.items():
            setattr(self, k, v)
        self._dibujar()

    def _soltar(self, evento):
        dentro = 0 <= evento.x <= self.winfo_width() and 0 <= evento.y <= self.winfo_height()
        fue_click = self.presionado and dentro
        self._estado(presionado=False)
        if fue_click:
            self.comando()

    def _dibujar(self):
        self.delete("all")
        ancho, alto = self.winfo_width(), self.winfo_height()
        if ancho < 2 or alto < 2:
            return
        r, s = self.RADIO, self.SOMBRA
        bajada = s - 1 if self.presionado else 0   # al presionar, el botón "se hunde"
        relleno = _aclarar(self.color) if self.encima and not self.presionado else self.color
        _rect_redondeado(self, 0, s, ancho - 1, alto - 1, r, fill=_oscurecer(self.color))
        _rect_redondeado(self, 0, bajada, ancho - 1, alto - 1 - s + bajada, r,
                         fill=relleno, outline=_aclarar(self.color, 0.25))
        self.create_text(ancho / 2, (alto - s) / 2 + bajada, text=self.texto,
                         fill=self.fg, font=self.fuente)


def _boton(parent, texto, comando, color, **opts):
    """Botón redondeado con color. `opts` admite padx, pady, font y fg."""
    return _BotonRedondeado(parent, texto, comando, color, **opts)


def _etiqueta(parent, texto, **opts):
    opts = {"bg": PANEL, "fg": TEXTO, "font": (FUENTE, 10), **opts}
    return tk.Label(parent, text=texto, **opts)


def _panel(parent, titulo):
    """Caja con borde y un título pequeño en mayúsculas."""
    caja = tk.Frame(parent, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
    _etiqueta(caja, titulo.upper(), fg=SUAVE, font=(FUENTE, 9, "bold")
              ).pack(anchor="w", padx=14, pady=(12, 6))
    return caja


def _tabla(parent, columnas, altura=8):
    """Treeview con barra de desplazamiento. columnas = [(id, título, ancho, ancla)]."""
    marco = tk.Frame(parent, bg=PANEL)
    tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings",
                         selectmode="browse", height=altura)
    for cid, titulo, ancho, ancla in columnas:
        tabla.heading(cid, text=titulo)
        tabla.column(cid, width=ancho, anchor=ancla, stretch=(cid == columnas[-1][0]))
    barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)
    tabla.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    return marco, tabla


class DialogoAgregar(tk.Toplevel):
    """Ventana pequeña para agregar una unidad, tipo o zona.
    Los errores se muestran dentro de la ventana, sin cerrarla."""

    def __init__(self, app, titulo, etiqueta, accion, opciones=()):
        super().__init__(app.root, bg=PANEL, padx=20, pady=16)
        self.app, self.accion = app, accion
        self.title(titulo)
        self.resizable(False, False)
        self.transient(app.root)

        _etiqueta(self, etiqueta).pack(anchor="w")
        self.texto = tk.StringVar()
        entrada = tk.Entry(self, textvariable=self.texto, width=32, bg=PANEL2, fg=TEXTO,
                           insertbackground=TEXTO, relief="flat", font=(FUENTE, 11),
                           highlightthickness=1, highlightbackground=BORDE, highlightcolor=AZUL)
        entrada.pack(fill="x", ipady=5, pady=(4, 10))

        self.marcas = {o: tk.BooleanVar() for o in opciones}   # casillas (si hay)
        if opciones:
            _etiqueta(self, "Tipos que puede atender:").pack(anchor="w")
        for o, var in self.marcas.items():
            tk.Checkbutton(self, text=o, variable=var, bg=PANEL, fg=TEXTO, selectcolor=PANEL2,
                           activebackground=PANEL, activeforeground=TEXTO,
                           highlightthickness=0, font=(FUENTE, 10)).pack(anchor="w")

        self.error = _etiqueta(self, "", fg=ROJO, wraplength=300, justify="left")
        self.error.pack(anchor="w", pady=(8, 0))
        fila = tk.Frame(self, bg=PANEL)
        fila.pack(fill="x", pady=(10, 0))
        _boton(fila, "Guardar", self._guardar, VERDE).pack(side="right")
        _boton(fila, "Cancelar", self.destroy, BORDE).pack(side="right", padx=8)

        self.bind("<Return>", lambda _e: self._guardar())
        self.bind("<Escape>", lambda _e: self.destroy())
        self._centrar()
        entrada.focus_set()
        self.grab_set()   # bloquea la ventana principal mientras esta está abierta

    def _centrar(self):
        """Coloca la ventanita en el centro de la ventana principal."""
        self.update_idletasks()
        raiz = self.app.root
        x = raiz.winfo_rootx() + (raiz.winfo_width() - self.winfo_reqwidth()) // 2
        y = raiz.winfo_rooty() + (raiz.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _guardar(self):
        marcadas = [o for o, var in self.marcas.items() if var.get()]
        resultado = self.accion(self.app.estado, self.texto.get(), marcadas)
        if resultado.ok:
            self.app._aplicar(resultado)
            self.destroy()
        else:
            self.error.config(text=resultado.mensaje)


class App:
    def __init__(self, root: tk.Tk, estado: n.Estado = None):
        self.root = root
        self.estado = estado or n.estado_inicial()
        root.title("Central de emergencias · Villa Paradigma")
        # La ventana nunca pide más alto que la pantalla (pantallas chicas o con zoom)
        alto = min(820, root.winfo_screenheight() - 80)
        root.geometry(f"1280x{alto}")
        root.minsize(1000, min(600, alto))
        root.configure(bg=FONDO)
        self._estilos()
        self._construir_encabezado()
        self._construir_area()
        self._construir_cuerpo()
        self._construir_zonas()
        self._construir_barra_estado()
        self._mensaje("Sistema listo. Registre una emergencia para comenzar.", True)
        self._refrescar()

    # ---------------------------------------------------------- Construcción
    def _estilos(self):
        s = ttk.Style(self.root)
        s.theme_use("clam")   # tema que permite cambiar colores
        s.configure("Treeview", background=PANEL2, fieldbackground=PANEL2, foreground=TEXTO,
                    rowheight=30, borderwidth=0, font=(FUENTE, 10),
                    bordercolor=PANEL2, lightcolor=PANEL2, darkcolor=PANEL2)
        s.configure("Treeview.Heading", background=PANEL, foreground=SUAVE, relief="flat",
                    font=(FUENTE, 9, "bold"))
        s.map("Treeview", background=[("selected", AZUL)], foreground=[("selected", "white")])
        s.map("Treeview.Heading", background=[("active", PANEL)])
        s.configure("TCombobox", fieldbackground=PANEL2, background=PANEL2, foreground=TEXTO,
                    arrowcolor=TEXTO, bordercolor=BORDE, lightcolor=PANEL2, darkcolor=PANEL2,
                    padding=5)
        s.map("TCombobox", fieldbackground=[("readonly", PANEL2)],
              foreground=[("readonly", TEXTO)], selectbackground=[("readonly", PANEL2)],
              selectforeground=[("readonly", TEXTO)])
        for estilo in ("TScrollbar", "Vertical.TScrollbar"):
            s.configure(estilo, background=BORDE, troughcolor=PANEL, bordercolor=PANEL,
                        lightcolor=BORDE, darkcolor=BORDE, arrowcolor=SUAVE, gripcount=0)
        # Colores de la lista desplegable de los combobox
        for opcion, valor in (("background", PANEL2), ("foreground", TEXTO),
                              ("selectBackground", AZUL), ("selectForeground", "white")):
            self.root.option_add(f"*TCombobox*Listbox.{opcion}", valor)

    def _construir_encabezado(self):
        enc = tk.Frame(self.root, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
        enc.grid(row=0, column=0, sticky="ew")
        self.root.columnconfigure(0, weight=1)

        tk.Frame(enc, bg=ROJO, width=6).pack(side="left", fill="y")    # franja de alarma
        titulos = tk.Frame(enc, bg=PANEL)
        titulos.pack(side="left", padx=16, pady=12)
        _etiqueta(titulos, "CENTRAL DE EMERGENCIAS", font=(FUENTE, 17, "bold")).pack(anchor="w")
        _etiqueta(titulos, "Villa Paradigma · Noche de tormenta", fg=SUAVE).pack(anchor="w")

        # Medidor de capacidad (a la derecha)
        medidor = tk.Frame(enc, bg=PANEL)
        medidor.pack(side="right", padx=20)
        self.lbl_capacidad = _etiqueta(medidor, "", font=(FUENTE, 11, "bold"))
        self.lbl_capacidad.pack(anchor="e")
        self.barra = tk.Canvas(medidor, width=240, height=12, bg=PANEL2, highlightthickness=0)
        self.barra.pack(pady=(4, 0))
        self.lbl_aviso = _etiqueta(medidor, "", fg=AMBAR, font=(FUENTE, 9))
        self.lbl_aviso.pack(anchor="e", pady=(4, 0))

    def _construir_area(self):
        """Zona central con desplazamiento vertical: si la ventana es más baja que
        el contenido (pantalla chica o con zoom) aparece una barra en lugar de
        cortar los paneles y sus botones."""
        marco = tk.Frame(self.root, bg=FONDO)
        marco.grid(row=1, column=0, sticky="nsew")
        self.root.rowconfigure(1, weight=1)
        self.lienzo = tk.Canvas(marco, bg=FONDO, highlightthickness=0, bd=0)
        self.barra_area = ttk.Scrollbar(marco, orient="vertical", command=self.lienzo.yview)
        self.lienzo.configure(yscrollcommand=self.barra_area.set)
        self.lienzo.pack(side="left", fill="both", expand=True)
        self.area = tk.Frame(self.lienzo, bg=FONDO)
        self.area.columnconfigure(0, weight=1)
        self.area.rowconfigure(0, weight=1)   # los paneles de arriba se estiran
        self.ventana_area = self.lienzo.create_window(0, 0, window=self.area, anchor="nw")
        self.lienzo.bind("<Configure>", lambda _e: self._ajustar_area())
        self.root.bind_all("<MouseWheel>", self._rueda)
        self.root.bind_all("<Button-4>", self._rueda)    # Linux
        self.root.bind_all("<Button-5>", self._rueda)

    def _ajustar_area(self):
        """El contenido ocupa al menos el alto visible; si no entra, se desplaza."""
        visible, necesario = self.lienzo.winfo_height(), self.area.winfo_reqheight()
        alto = max(visible, necesario)
        self.lienzo.itemconfigure(self.ventana_area, width=self.lienzo.winfo_width(), height=alto)
        self.lienzo.configure(scrollregion=(0, 0, self.lienzo.winfo_width(), alto))
        if necesario > visible:
            if not self.barra_area.winfo_ismapped():
                self.barra_area.pack(side="right", fill="y")
        elif self.barra_area.winfo_ismapped():
            self.barra_area.pack_forget()
            self.lienzo.yview_moveto(0)

    def _rueda(self, evento):
        """Rueda del mouse: mueve la página, salvo sobre listas o desplegables
        (que tienen su propio desplazamiento) o en otras ventanas."""
        w = evento.widget
        if (isinstance(w, str) or isinstance(w, (ttk.Treeview, ttk.Combobox))
                or w.winfo_toplevel() is not self.root or not self.barra_area.winfo_ismapped()):
            return
        arriba = evento.num == 4 or getattr(evento, "delta", 0) > 0
        self.lienzo.yview_scroll(-1 if arriba else 1, "units")

    def _construir_cuerpo(self):
        cuerpo = tk.Frame(self.area, bg=FONDO)
        cuerpo.grid(row=0, column=0, sticky="nsew", padx=14, pady=(14, 0))
        cuerpo.columnconfigure(1, weight=1)   # la lista central se estira
        cuerpo.rowconfigure(0, weight=1, minsize=360)

        self._construir_formulario(cuerpo).grid(row=0, column=0, sticky="ns")
        self._construir_lista(cuerpo).grid(row=0, column=1, sticky="nsew", padx=12)
        self._construir_unidades(cuerpo).grid(row=0, column=2, sticky="ns")

    def _construir_formulario(self, padre):
        caja = _panel(padre, "Nueva emergencia")
        interior = tk.Frame(caja, bg=PANEL)
        interior.pack(fill="x", padx=14, pady=(0, 14))
        self.var_tipo, self.var_zona, self.var_gravedad = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.cb_tipo = self._campo(interior, "Tipo", self.var_tipo)
        self.cb_zona = self._campo(interior, "Zona", self.var_zona)
        self.cb_gravedad = self._campo(interior, "Gravedad", self.var_gravedad)
        _boton(interior, "REGISTRAR EMERGENCIA", self._registrar, ROJO
               ).pack(fill="x", pady=(16, 0))

        # --- Ajustes (escalabilidad): todo se puede cambiar sin tocar el código ---
        _etiqueta(caja, "AJUSTES DEL SISTEMA", fg=SUAVE, font=(FUENTE, 9, "bold")
                  ).pack(anchor="w", padx=14, pady=(10, 6))
        ajustes = tk.Frame(caja, bg=PANEL)
        ajustes.pack(fill="x", padx=14, pady=(0, 14))
        fila = tk.Frame(ajustes, bg=PANEL)
        fila.pack(fill="x")
        for texto, accion in (("+ Unidad", self._dialogo_unidad),
                              ("+ Tipo", self._dialogo_tipo),
                              ("+ Zona", self._dialogo_zona)):
            _boton(fila, texto, accion, BORDE, padx=8, pady=5).pack(side="left", expand=True,
                                                                      fill="x", padx=2)
        _boton(ajustes, "Cambiar capacidad…", self._cambiar_capacidad, BORDE, pady=5
               ).pack(fill="x", pady=(8, 0), padx=2)
        _etiqueta(ajustes, "Si se llena el tope:", fg=SUAVE).pack(anchor="w", pady=(10, 2))
        self.cb_politica = ttk.Combobox(ajustes, state="readonly",
                                        values=list(ETIQUETAS_POLITICA.values()))
        self.cb_politica.pack(fill="x")
        self.cb_politica.bind("<<ComboboxSelected>>", self._elegir_politica)
        return caja

    def _campo(self, padre, titulo, variable):
        _etiqueta(padre, titulo, fg=SUAVE).pack(anchor="w", pady=(10, 2))
        cb = ttk.Combobox(padre, textvariable=variable, state="readonly", width=24)
        cb.pack(fill="x")
        return cb

    def _construir_lista(self, padre):
        caja = _panel(padre, "Emergencias abiertas (más urgentes arriba)")
        marco, self.tabla = _tabla(caja, [("id", "#", 40, "center"), ("gravedad", "Gravedad", 105, "w"),
                                          ("tipo", "Tipo", 85, "w"), ("zona", "Zona", 75, "w"),
                                          ("estado", "Estado", 190, "w")], altura=8)
        # Los botones se empaquetan ANTES que la tabla (abajo): así nunca quedan
        # cortados aunque la ventana sea baja; la que se achica es la tabla.
        botones = tk.Frame(caja, bg=PANEL)
        botones.pack(side="bottom", fill="x", padx=14, pady=14)
        marco.pack(fill="both", expand=True, padx=14)
        # Aviso que se ve solo cuando no hay emergencias
        self.lbl_vacio = _etiqueta(marco, "Sin emergencias abiertas", fg=SUAVE, bg=PANEL2,
                                   font=(FUENTE, 11))
        _boton(botones, "ASIGNAR UNIDAD A LA MÁS URGENTE", self._asignar, AZUL
               ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        _boton(botones, "CERRAR SELECCIONADA", self._cerrar, VERDE
               ).pack(side="left", expand=True, fill="x", padx=(6, 0))
        return caja

    def _construir_unidades(self, padre):
        caja = _panel(padre, "Unidades")
        marco, self.tabla_unidades = _tabla(
            caja, [("nombre", "Unidad", 140, "w"), ("estado", "Estado", 115, "w"),
                   ("atiende", "Atiende", 130, "w")])
        marco.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        return caja

    def _construir_zonas(self):
        caja = _panel(self.area, "Resumen por zona")
        caja.grid(row=1, column=0, sticky="ew", padx=14, pady=14)
        self.marco_zonas = tk.Frame(caja, bg=PANEL)
        self.marco_zonas.pack(fill="x", padx=14, pady=(0, 14))

    def _construir_barra_estado(self):
        self.lbl_estado = tk.Label(self.root, text="", anchor="w", bg=PANEL, fg=TEXTO,
                                   font=(FUENTE, 10), padx=16, pady=8)
        self.lbl_estado.grid(row=2, column=0, sticky="ew")

    # ------------------------------------------------------------ Acciones
    def _aplicar(self, resultado: n.Resultado) -> bool:
        """Único punto por donde cambia el estado: guarda, avisa y redibuja."""
        self.estado = resultado.estado
        self._mensaje(resultado.mensaje, resultado.ok)
        self._refrescar()
        return resultado.ok

    def _mensaje(self, texto: str, ok: bool):
        self.lbl_estado.config(text=("✔  " if ok else "✖  ") + texto, fg=VERDE if ok else ROJO)

    def _registrar(self):
        if not (self.var_tipo.get() and self.var_zona.get() and self.var_gravedad.get()):
            return self._mensaje("Complete tipo, zona y gravedad antes de registrar.", False)
        self._aplicar(n.registrar(self.estado, self.var_tipo.get(),
                                  self.var_zona.get(), self.var_gravedad.get()))

    def _asignar(self):
        self._aplicar(n.asignar(self.estado))

    def _cerrar(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return self._mensaje("Seleccione primero una emergencia de la lista.", False)
        self._aplicar(n.cerrar(self.estado, int(seleccion[0])))   # el iid es el id

    def _dialogo_unidad(self):
        DialogoAgregar(self, "Agregar unidad", "Nombre de la unidad:",
                       lambda est, texto, marcadas: n.agregar_unidad(est, texto, marcadas),
                       opciones=self.estado.tipos)

    def _dialogo_tipo(self):
        DialogoAgregar(self, "Agregar tipo de emergencia", "Nombre del tipo (ej. inundación):",
                       lambda est, texto, _m: n.agregar_tipo(est, texto))

    def _dialogo_zona(self):
        DialogoAgregar(self, "Agregar zona", "Nombre de la zona:",
                       lambda est, texto, _m: n.agregar_zona(est, texto))

    def _cambiar_capacidad(self):
        valor = simpledialog.askinteger(
            "Capacidad", f"Máximo de emergencias abiertas (1 a {n.CAPACIDAD_MAXIMA}):",
            parent=self.root, initialvalue=self.estado.capacidad,
            minvalue=1, maxvalue=n.CAPACIDAD_MAXIMA)
        if valor is not None:   # None = el usuario canceló
            self._aplicar(n.cambiar_capacidad(self.estado, valor))

    def _elegir_politica(self, _evento):
        por_etiqueta = {v: k for k, v in ETIQUETAS_POLITICA.items()}
        self._aplicar(n.cambiar_politica(self.estado, por_etiqueta[self.cb_politica.get()]))

    # ------------------------------------------------------------- Dibujo
    def _color_gravedad(self, gravedad: str) -> str:
        """Verde la menos grave, rojo la más grave, ámbar las intermedias.
        Se calcula por posición, así funciona aunque se agreguen gravedades."""
        total = len(self.estado.gravedades) - 1
        fraccion = n.peso(self.estado, gravedad) / total if total else 0
        return VERDE if fraccion < 0.34 else AMBAR if fraccion < 0.67 else ROJO

    def _refrescar(self):
        """Redibuja TODA la pantalla a partir del estado actual."""
        est = self.estado
        self.cb_tipo["values"], self.cb_zona["values"] = est.tipos, est.zonas
        self.cb_gravedad["values"] = est.gravedades
        self.cb_politica.set(ETIQUETAS_POLITICA[est.politica_tope])
        self._dibujar_capacidad()
        self._dibujar_emergencias()
        self._dibujar_unidades()
        self._dibujar_zonas()

    def _dibujar_capacidad(self):
        est, abiertas = self.estado, len(self.estado.emergencias)
        fraccion = min(1, abiertas / est.capacidad)
        color = ROJO if fraccion >= 1 else AMBAR if fraccion >= 0.7 else VERDE
        self.lbl_capacidad.config(text=f"Abiertas  {abiertas} / {est.capacidad}"
                                       + ("   · TOPE ALCANZADO" if abiertas >= est.capacidad else ""),
                                  fg=color)
        self.barra.delete("all")
        self.barra.create_rectangle(0, 0, int(240 * fraccion), 12, fill=color, width=0)
        sin_cobertura = n.tipos_sin_cobertura(est)
        self.lbl_aviso.config(text=("Sin unidad para: " + ", ".join(sin_cobertura))
                              if sin_cobertura else "")

    def _dibujar_emergencias(self):
        previa = self.tabla.selection()               # para conservar la selección
        self.tabla.delete(*self.tabla.get_children())
        est = self.estado
        for g in est.gravedades:                      # una etiqueta de color por gravedad
            self.tabla.tag_configure(f"g_{g}", foreground=self._color_gravedad(g))
        self.tabla.tag_configure("atencion", foreground=SUAVE)
        for e in n.pendientes(est):
            # Cambio 2: si subió por la espera, se muestra la nueva y la original
            g = n.gravedad_efectiva(est, e)
            subio = g != e.gravedad
            self.tabla.insert("", "end", iid=str(e.id), tags=(f"g_{g}",),
                              values=(e.id, g.upper() + (" ↑" if subio else ""), e.tipo, e.zona,
                                      f"Pendiente · era {e.gravedad}, subió por espera"
                                      if subio else "Pendiente"))
        for e in sorted(n.en_atencion(est), key=lambda x: x.id):
            self.tabla.insert("", "end", iid=str(e.id), tags=("atencion",),
                              values=(e.id, e.gravedad.upper(), e.tipo, e.zona,
                                      f"→ {e.unidad}"))
        if previa and self.tabla.exists(previa[0]):
            self.tabla.selection_set(previa[0])
        if est.emergencias:
            self.lbl_vacio.place_forget()
        else:
            self.lbl_vacio.place(relx=0.5, rely=0.5, anchor="center")

    def _dibujar_unidades(self):
        t = self.tabla_unidades
        t.delete(*t.get_children())
        t.tag_configure("libre", foreground=VERDE)
        t.tag_configure("ocupada", foreground=ROJO)
        asignadas = {e.unidad: e.id for e in n.en_atencion(self.estado)}
        for u in self.estado.unidades:
            estado_u = f"● Ocupada #{asignadas[u.nombre]}" if u.ocupada else "● Libre"
            t.insert("", "end", values=(u.nombre, estado_u, ", ".join(u.atiende)
                                     + (f" (solo {', '.join(u.zonas)})" if u.zonas else "")),
                     tags=("ocupada" if u.ocupada else "libre",))

    def _dibujar_zonas(self):
        for tarjeta in self.marco_zonas.winfo_children():
            tarjeta.destroy()
        for i, (zona, pend, aten) in enumerate(n.resumen_por_zona(self.estado)):
            fila, col = divmod(i, ZONAS_POR_FILA)
            self.marco_zonas.columnconfigure(col, weight=1, uniform="zona")
            # Borde rojo si la zona tiene emergencias sin atender
            tarjeta = tk.Frame(self.marco_zonas, bg=PANEL2, highlightthickness=2,
                               highlightbackground=ROJO if pend else BORDE)
            tarjeta.grid(row=fila, column=col, sticky="ew", padx=4, pady=4)
            _etiqueta(tarjeta, zona, bg=PANEL2, font=(FUENTE, 11, "bold")).pack(pady=(8, 0))
            _etiqueta(tarjeta, f"{pend} pendientes", bg=PANEL2, fg=ROJO if pend else SUAVE
                      ).pack()
            _etiqueta(tarjeta, f"{aten} en atención", bg=PANEL2, fg=AZUL if aten else SUAVE
                      ).pack(pady=(0, 8))
        # Si aparecen más filas de tarjetas, se recalcula el desplazamiento
        self.root.update_idletasks()
        self._ajustar_area()


def iniciar():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    iniciar()
