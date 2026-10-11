import os
import ssl

# ---------------------------------------------------------
# EVITAR PROBLEMAS SSL
# ---------------------------------------------------------

if (not os.environ.get('PYTHONHTTPSVERIFY', '')
        and getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


import requests
from bs4 import BeautifulSoup
import sqlite3
import tkinter as tk
from tkinter import messagebox


# =========================================================
# CONFIGURACIÓN
# =========================================================

URL_BASE = "https://www.vinissimus.com/es/vinos/tinto/?cursor="

# El ejercicio pide al menos 3 páginas.
# Cada página aumenta el cursor en 36.
CURSORES = [0, 36, 72]


# =========================================================
# BASE DE DATOS
# =========================================================

conexion = sqlite3.connect("vinos.db")
cursor_db = conexion.cursor()


def crear_base_datos():

    cursor_db.execute("""
        CREATE TABLE IF NOT EXISTS vinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL,
            denominacion TEXT,
            bodega TEXT,
            uvas TEXT
        )
    """)

    conexion.commit()


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def limpiar_texto(texto):
    """
    Elimina espacios innecesarios.
    """
    if texto is None:
        return ""

    return " ".join(texto.split())


def convertir_precio(texto):
    """
    Convierte textos como:

        15,95 €
        15.95 €
        15,95

    en un número float.
    """

    if not texto:
        return None

    texto = texto.replace("€", "")
    texto = texto.replace("\xa0", " ")
    texto = texto.strip()

    # Dejamos solamente números, coma y punto
    permitido = "0123456789,."

    texto = "".join(
        caracter for caracter in texto
        if caracter in permitido
    )

    if not texto:
        return None

    # Si tenemos 12,95 -> 12.95
    texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return None


# =========================================================
# EXTRAER PRECIO
# =========================================================

def obtener_precio(producto):

    """
    Intenta localizar el precio actual.

    Es importante que se utilice el precio rebajado si
    existe un descuento.
    """

    selectores = [
        ".price",
        ".product-price",
        ".current-price",
        "[class*='price']"
    ]

    # Primero buscamos un precio que indique oferta/descuento
    elementos = producto.find_all(
        class_=lambda x: x and (
            "price" in " ".join(x).lower()
        )
    )

    precios = []

    for elemento in elementos:

        texto = limpiar_texto(
            elemento.get_text(" ", strip=True)
        )

        precio = convertir_precio(texto)

        if precio is not None:
            precios.append((elemento, precio, texto))

    if not precios:
        return None

    # Preferimos un elemento que tenga alguna referencia
    # a precio actual/oferta/venta.
    for elemento, precio, texto in precios:

        clases = " ".join(elemento.get("class", [])).lower()

        if (
            "current" in clases
            or "sale" in clases
            or "offer" in clases
            or "discount" in clases
        ):
            return precio

    # Si no se ha identificado un precio rebajado,
    # utilizamos el primer precio encontrado.
    return precios[0][1]


# =========================================================
# EXTRAER INFORMACIÓN DE UN PRODUCTO
# =========================================================

def extraer_vino(producto):

    nombre = ""
    precio = None
    denominacion = ""
    bodega = ""
    uvas = ""

    # -----------------------------------------------------
    # NOMBRE
    # -----------------------------------------------------

    posibles_nombres = [
        "h2",
        "h3",
        ".product-name",
        ".name",
        "[class*='product-name']"
    ]

    for selector in posibles_nombres:

        elemento = producto.select_one(selector)

        if elemento:

            texto = limpiar_texto(
                elemento.get_text(" ", strip=True)
            )

            if texto:
                nombre = texto
                break

    # -----------------------------------------------------
    # PRECIO
    # -----------------------------------------------------

    precio = obtener_precio(producto)

    # -----------------------------------------------------
    # RESTO DE INFORMACIÓN
    # -----------------------------------------------------

    texto_completo = limpiar_texto(
        producto.get_text(" ", strip=True)
    )

    # -----------------------------------------------------
    # BODEGA
    # -----------------------------------------------------

    elementos_bodega = producto.find_all(
        string=lambda texto:
        texto and "Bodega" in texto
    )

    if elementos_bodega:

        elemento = elementos_bodega[0]

        padre = elemento.parent

        if padre:
            bodega = limpiar_texto(
                padre.get_text(" ", strip=True)
            )

    # Intentamos también mediante clases
    if not bodega:

        for selector in [
            ".winery",
            ".cellar",
            ".bodega",
            "[class*='winery']",
            "[class*='cellar']"
        ]:

            elemento = producto.select_one(selector)

            if elemento:

                bodega = limpiar_texto(
                    elemento.get_text(" ", strip=True)
                )

                if bodega:
                    break

    # -----------------------------------------------------
    # DENOMINACIÓN
    # -----------------------------------------------------

    elementos_region = producto.find_all(
        string=lambda texto:
        texto and (
            "Rioja" in texto
            or "Ribera del Duero" in texto
            or "Priorat" in texto
            or "Bierzo" in texto
            or "Rueda" in texto
            or "Toro" in texto
        )
    )

    if elementos_region:

        denominacion = limpiar_texto(
            elementos_region[0]
        )

    if not denominacion:

        for selector in [
            ".region",
            ".denomination",
            ".denominacion",
            "[class*='region']",
            "[class*='denomination']"
        ]:

            elemento = producto.select_one(selector)

            if elemento:

                denominacion = limpiar_texto(
                    elemento.get_text(" ", strip=True)
                )

                if denominacion:
                    break

    # -----------------------------------------------------
    # UVAS
    # -----------------------------------------------------

    enlaces_uva = []

    for enlace in producto.find_all("a", href=True):

        href = enlace["href"]

        if "/es/uva/" in href:

            texto_uva = limpiar_texto(
                enlace.get_text(" ", strip=True)
            )

            if texto_uva:
                enlaces_uva.append(texto_uva)

    # Eliminamos duplicados
    uvas_lista = []

    for uva in enlaces_uva:

        if uva not in uvas_lista:
            uvas_lista.append(uva)

    uvas = ", ".join(uvas_lista)

    return {
        "nombre": nombre,
        "precio": precio,
        "denominacion": denominacion,
        "bodega": bodega,
        "uvas": uvas
    }


# =========================================================
# GUARDAR UN VINO
# =========================================================

def guardar_vino(vino):

    # Evitamos guardar productos sin nombre
    if not vino["nombre"]:
        return False

    cursor_db.execute("""
        INSERT INTO vinos
        (nombre, precio, denominacion, bodega, uvas)
        VALUES (?, ?, ?, ?, ?)
    """, (
        vino["nombre"],
        vino["precio"],
        vino["denominacion"],
        vino["bodega"],
        vino["uvas"]
    ))

    return True


# =========================================================
# CARGAR VINOS
# =========================================================

def cargar_vinos():

    # -----------------------------------------------------
    # BORRAMOS LOS DATOS ANTERIORES
    # -----------------------------------------------------

    respuesta = messagebox.askyesno(
        "Cargar vinos",
        "¿Quieres cargar nuevamente los vinos?\n\n"
        "Se eliminarán los datos anteriores."
    )

    if not respuesta:
        return

    cursor_db.execute("DELETE FROM vinos")
    conexion.commit()

    total = 0

    # -----------------------------------------------------
    # RECORREMOS LAS 3 PÁGINAS
    # -----------------------------------------------------

    for cursor in CURSORES:

        url = URL_BASE + str(cursor)

        try:

            respuesta = requests.get(
                url,
                timeout=30
            )

            respuesta.raise_for_status()

        except requests.RequestException as error:

            messagebox.showerror(
                "Error",
                f"No se ha podido acceder a:\n{url}\n\n"
                f"{error}"
            )

            return

        # -------------------------------------------------
        # BEAUTIFULSOUP
        # -------------------------------------------------

        soup = BeautifulSoup(
            respuesta.text,
            "html.parser"
        )

        # -------------------------------------------------
        # BUSCAMOS PRODUCTOS
        # -------------------------------------------------

        productos = soup.select(
            ".product-list-item"
        )

        # En la página puede aparecer el esqueleto mientras
        # los productos se cargan dinámicamente.
        #
        # No contamos los skeleton como productos.
        productos = [
            producto
            for producto in productos
            if "skeleton" not in " ".join(
                producto.get("class", [])
            ).lower()
        ]

        # -------------------------------------------------
        # PROCESAMOS LOS PRODUCTOS
        # -------------------------------------------------

        for producto in productos:

            vino = extraer_vino(producto)

            if guardar_vino(vino):
                total += 1

    conexion.commit()

    # -----------------------------------------------------
    # MOSTRAMOS RESULTADO
    # -----------------------------------------------------

    messagebox.showinfo(
        "Carga terminada",
        f"Se han almacenado {total} vinos "
        f"en la base de datos."
    )


# =========================================================
# VENTANA PARA MOSTRAR RESULTADOS
# =========================================================

def ventana_resultados(titulo, vinos):

    ventana = tk.Toplevel()
    ventana.title(titulo)
    ventana.geometry("900x500")

    # -----------------------------------------------------
    # FRAME
    # -----------------------------------------------------

    frame = tk.Frame(ventana)
    frame.pack(
        fill=tk.BOTH,
        expand=True,
        padx=10,
        pady=10
    )

    # -----------------------------------------------------
    # LISTBOX
    # -----------------------------------------------------

    lista = tk.Listbox(
        frame,
        font=("Arial", 10)
    )

    lista.pack(
        side=tk.LEFT,
        fill=tk.BOTH,
        expand=True
    )

    # -----------------------------------------------------
    # SCROLLBAR
    # -----------------------------------------------------

    scrollbar = tk.Scrollbar(
        frame,
        orient=tk.VERTICAL,
        command=lista.yview
    )

    scrollbar.pack(
        side=tk.RIGHT,
        fill=tk.Y
    )

    lista.config(
        yscrollcommand=scrollbar.set
    )

    # -----------------------------------------------------
    # INSERTAMOS LOS VINOS
    # -----------------------------------------------------

    for vino in vinos:

        lista.insert(
            tk.END,
            vino
        )


# =========================================================
# LISTAR TODOS LOS VINOS
# =========================================================

def listar_vinos():

    cursor_db.execute("""
        SELECT nombre, precio, bodega, denominacion
        FROM vinos
        ORDER BY nombre
    """)

    resultados = cursor_db.fetchall()

    if not resultados:

        messagebox.showinfo(
            "Listar",
            "No hay vinos almacenados."
        )

        return

    vinos = []

    for nombre, precio, bodega, denominacion in resultados:

        if precio is None:
            precio_texto = "Sin precio"
        else:
            precio_texto = f"{precio:.2f} €"

        texto = (
            f"{nombre} | "
            f"{precio_texto} | "
            f"{bodega} | "
            f"{denominacion}"
        )

        vinos.append(texto)

    ventana_resultados(
        "Todos los vinos",
        vinos
    )


# =========================================================
# BUSCAR POR DENOMINACIÓN
# =========================================================

def buscar_denominacion():

    cursor_db.execute("""
        SELECT DISTINCT denominacion
        FROM vinos
        WHERE denominacion <> ''
        ORDER BY denominacion
    """)

    denominaciones = [
        fila[0]
        for fila in cursor_db.fetchall()
    ]

    if not denominaciones:

        messagebox.showinfo(
            "Denominación",
            "No hay denominaciones almacenadas."
        )

        return

    ventana = tk.Toplevel()
    ventana.title("Buscar por denominación")
    ventana.geometry("400x180")

    tk.Label(
        ventana,
        text="Seleccione una denominación:"
    ).pack(pady=10)

    valor = tk.StringVar()
    valor.set(denominaciones[0])

    spinbox = tk.Spinbox(
        ventana,
        values=denominaciones,
        textvariable=valor,
        width=35
    )

    spinbox.pack(pady=10)

    def buscar():

        denominacion = valor.get()

        cursor_db.execute("""
            SELECT nombre, precio, bodega, denominacion
            FROM vinos
            WHERE denominacion = ?
            ORDER BY nombre
        """, (denominacion,))

        resultados = cursor_db.fetchall()

        vinos = []

        for nombre, precio, bodega, denominacion in resultados:

            precio_texto = (
                f"{precio:.2f} €"
                if precio is not None
                else "Sin precio"
            )

            vinos.append(
                f"{nombre} | "
                f"{precio_texto} | "
                f"{bodega} | "
                f"{denominacion}"
            )

        ventana_resultados(
            f"Vinos de {denominacion}",
            vinos
        )

    tk.Button(
        ventana,
        text="Buscar",
        command=buscar
    ).pack(pady=10)


# =========================================================
# BUSCAR POR PRECIO
# =========================================================

def buscar_precio():

    ventana = tk.Toplevel()
    ventana.title("Buscar por precio")
    ventana.geometry("400x180")

    tk.Label(
        ventana,
        text="Introduzca un precio máximo:"
    ).pack(pady=15)

    entrada = tk.Entry(
        ventana,
        width=20
    )

    entrada.pack()

    def buscar():

        try:

            precio_maximo = float(
                entrada.get().replace(",", ".")
            )

        except ValueError:

            messagebox.showerror(
                "Error",
                "Introduzca un precio válido."
            )

            return

        cursor_db.execute("""
            SELECT nombre, precio, bodega, denominacion
            FROM vinos
            WHERE precio IS NOT NULL
              AND precio < ?
            ORDER BY precio ASC
        """, (precio_maximo,))

        resultados = cursor_db.fetchall()

        vinos = []

        for nombre, precio, bodega, denominacion in resultados:

            vinos.append(
                f"{nombre} | "
                f"{precio:.2f} € | "
                f"{bodega} | "
                f"{denominacion}"
            )

        ventana_resultados(
            f"Vinos por debajo de {precio_maximo:.2f} €",
            vinos
        )

    tk.Button(
        ventana,
        text="Buscar",
        command=buscar
    ).pack(pady=15)


# =========================================================
# BUSCAR POR UVA
# =========================================================

def buscar_uva():

    cursor_db.execute("""
        SELECT uvas
        FROM vinos
        WHERE uvas <> ''
    """)

    filas = cursor_db.fetchall()

    uvas = []

    for fila in filas:

        texto = fila[0]

        partes = texto.split(",")

        for parte in partes:

            uva = parte.strip()

            if uva and uva not in uvas:
                uvas.append(uva)

    uvas.sort()

    if not uvas:

        messagebox.showinfo(
            "Uvas",
            "No hay tipos de uva almacenados."
        )

        return

    ventana = tk.Toplevel()
    ventana.title("Buscar por uva")
    ventana.geometry("400x180")

    tk.Label(
        ventana,
        text="Seleccione un tipo de uva:"
    ).pack(pady=10)

    valor = tk.StringVar()
    valor.set(uvas[0])

    spinbox = tk.Spinbox(
        ventana,
        values=uvas,
        textvariable=valor,
        width=35
    )

    spinbox.pack(pady=10)

    def buscar():

        uva = valor.get()

        # % permite buscar la uva dentro del campo uvas
        cursor_db.execute("""
            SELECT nombre, uvas
            FROM vinos
            WHERE LOWER(uvas) LIKE LOWER(?)
            ORDER BY nombre
        """, (
            "%" + uva + "%",
        ))

        resultados = cursor_db.fetchall()

        vinos = []

        for nombre, tipos_uvas in resultados:

            vinos.append(
                f"{nombre} | "
                f"Uva buscada: {uva} | "
                f"Tipos de uvas: {tipos_uvas}"
            )

        ventana_resultados(
            f"Vinos con {uva}",
            vinos
        )

    tk.Button(
        ventana,
        text="Buscar",
        command=buscar
    ).pack(pady=10)


# =========================================================
# SALIR
# =========================================================

def salir():

    conexion.close()
    ventana.destroy()


# =========================================================
# VENTANA PRINCIPAL
# =========================================================

crear_base_datos()

ventana = tk.Tk()

ventana.title(
    "Acceso inteligente a la información - Vinos"
)

ventana.geometry("600x400")


# =========================================================
# MENÚ
# =========================================================

barra_menu = tk.Menu(ventana)


# ---------------------------------------------------------
# MENÚ DATOS
# ---------------------------------------------------------

menu_datos = tk.Menu(
    barra_menu,
    tearoff=0
)

menu_datos.add_command(
    label="Cargar",
    command=cargar_vinos
)

menu_datos.add_command(
    label="Listar",
    command=listar_vinos
)

menu_datos.add_separator()

menu_datos.add_command(
    label="Salir",
    command=salir
)

barra_menu.add_cascade(
    label="Datos",
    menu=menu_datos
)


# ---------------------------------------------------------
# MENÚ BUSCAR
# ---------------------------------------------------------

menu_buscar = tk.Menu(
    barra_menu,
    tearoff=0
)

menu_buscar.add_command(
    label="Denominación",
    command=buscar_denominacion
)

menu_buscar.add_command(
    label="Precio",
    command=buscar_precio
)

menu_buscar.add_command(
    label="Uvas",
    command=buscar_uva
)

barra_menu.add_cascade(
    label="Buscar",
    menu=menu_buscar
)


# ---------------------------------------------------------
# INSTALAMOS EL MENÚ
# ---------------------------------------------------------

ventana.config(
    menu=barra_menu
)


# =========================================================
# TEXTO DE LA VENTANA PRINCIPAL
# =========================================================

titulo = tk.Label(
    ventana,
    text="ACCESO INTELIGENTE A LA INFORMACIÓN",
    font=("Arial", 16, "bold")
)

titulo.pack(pady=60)

subtitulo = tk.Label(
    ventana,
    text="Ejercicio BeautifulSoup I\n\n"
         "Utilice el menú Datos o Buscar",
    font=("Arial", 12)
)

subtitulo.pack()


# =========================================================
# EJECUTAMOS LA APLICACIÓN
# =========================================================

ventana.mainloop()