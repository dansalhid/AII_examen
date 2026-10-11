from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
import os
import ssl
from datetime import datetime


meses = {
    "enero": "1",
    "febrero": "2",
    "marzo": "3",
    "abril": "4",
    "mayo": "5",
    "junio": "6",
    "julio": "7",
    "agosto": "8",
    "septiembre": "9",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12"
}


if (
    not os.environ.get("PYTHONHTTPSVERIFY", "")
    and getattr(ssl, "_create_unverified_context", None)
):
    ssl._create_default_https_context = ssl._create_unverified_context


def cargar():
    respuesta = messagebox.askyesno(
        title="Confirmar",
        message=(
            "¿Está seguro que quiere recargar los datos?\n"
            "Esta operación puede ser lenta."
        )
    )

    if respuesta:
        almacenar_bd()


def almacenar_bd():
    conn = sqlite3.connect("recetas.db")
    conn.text_factory = str

    try:
        conn.execute("DROP TABLE IF EXISTS RECETAS")

        conn.execute("""
            CREATE TABLE RECETAS (
                TITULO TEXT NOT NULL,
                DIFICULTAD TEXT,
                COMENSALES INT,
                TIEMPO INT,
                AUTOR TEXT,
                FECHA DATE
            );
        """)

        f = urllib.request.urlopen(
            "https://www.recetasgratis.net/"
            "Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
        )

        s = BeautifulSoup(f, "lxml")

        lista = s.find(
            "section",
            class_="max_width margin-top-1 resultados hasaside"
        )

        if lista is None:
            messagebox.showerror(
                "Error",
                "No se ha encontrado la lista de recetas."
            )
            return

        lista_recetas = lista.find_all(
            "div",
            class_="resultado link"
        )

        for receta in lista_recetas:
            url = receta.a["href"]

            f = urllib.request.urlopen(url)
            s = BeautifulSoup(f, "lxml")

            article = s.find(
                "article",
                class_="columna-post"
            )

            if article:
                # Extraemos el título
                h1_tag = article.find("h1")

                titulo = (
                    h1_tag.text.strip()
                    if h1_tag
                    else "Sin título"
                )

                # Información del autor y fecha
                header = article.find(
                    "header",
                    class_="header-post"
                )

                autor = ""
                fecha = ""

                if header:
                    info_articulo = header.find(
                        "div",
                        class_="info_articulo"
                    )

                    if info_articulo:
                        nombre_autor = info_articulo.find(
                            "div",
                            class_="nombre_autor"
                        )

                        if nombre_autor:
                            autor_tag = nombre_autor.find("a")

                            if autor_tag:
                                autor = autor_tag.get_text(
                                    strip=True
                                )

                            fecha_tag = nombre_autor.find(
                                "span",
                                class_="date_publish"
                            )

                            if fecha_tag:
                                fecha = fecha_tag.get_text(
                                    strip=True
                                )

                # Valores por defecto
                dificultad = "NO"
                unidades = "0"
                tiempo = "0"

                recipe_info = article.find(
                    "div",
                    class_="recipe-info"
                )

                if recipe_info:
                    properties = recipe_info.find(
                        "div",
                        class_="properties"
                    )

                    if properties:
                        span_dif = properties.find(
                            "span",
                            class_="property dificultad"
                        )

                        span_un = properties.find(
                            "span",
                            class_="property unidades"
                        )

                        span_ti = properties.find(
                            "span",
                            class_="property duracion"
                        )

                        if span_dif:
                            dificultad = span_dif.text.strip()

                        if span_un:
                            unidades = span_un.text.strip()

                        if span_ti:
                            tiempo = span_ti.text.strip()

                # Convertimos comensales a entero
                if unidades != "0":
                    unidades = int(unidades.split()[0])

                # Convertimos el tiempo a minutos
                if tiempo != "0":
                    tiempo = convertir_a_minutos(tiempo)

                # Procesamos la fecha
                fecha_dt = None

                if fecha:
                    limpio = (
                        fecha.lower()
                        .replace("de", "")
                        .replace("actualizado:", "")
                        .strip()
                    )

                    palabras = limpio.split()

                    if len(palabras) >= 3:
                        # Tomamos día, mes y año desde el final
                        dia = palabras[-3]
                        mes_nombre = palabras[-2]
                        anio = palabras[-1]

                        # Comprobamos que el mes exista
                        if mes_nombre in meses:
                            mes_num = meses[mes_nombre]

                            cadena_numerica = (
                                f"{dia} {mes_num} {anio}"
                            )

                            fecha_dt = datetime.strptime(
                                cadena_numerica,
                                "%d %m %Y"
                            )

                            print(fecha_dt)
                        else:
                            print(
                                f"Error: El mes '{mes_nombre}' "
                                "no está en el diccionario."
                            )

                print(
                    f"Receta: {titulo} | "
                    f"Dificultad: {dificultad} | "
                    f"Unidades: {unidades} | "
                    f"Tiempo: {tiempo} | "
                    f"Autor: {autor} | "
                    f"Fecha: {fecha_dt}"
                )

                conn.execute(
                    """
                    INSERT INTO RECETAS
                    (
                        TITULO,
                        DIFICULTAD,
                        COMENSALES,
                        TIEMPO,
                        AUTOR,
                        FECHA
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        titulo,
                        dificultad,
                        unidades,
                        tiempo,
                        autor,
                        fecha_dt
                    )
                )

        conn.commit()

        cursor = conn.execute(
            "SELECT COUNT(*) FROM RECETAS"
        )

        total = cursor.fetchone()[0]

        messagebox.showinfo(
            "Base de Datos",
            "Base de datos creada correctamente.\n"
            "Hay " + str(total) + " registros."
        )

    except Exception as e:
        messagebox.showerror(
            "Error",
            "No se pudieron cargar los datos:\n" + str(e)
        )

    finally:
        conn.close()


def convertir_a_minutos(texto_tiempo):
    if not texto_tiempo:
        return None

    # Pasamos a minúsculas
    texto = texto_tiempo.lower().strip()

    total_minutos = 0

    # Procesamos las horas
    if "h" in texto:
        partes_h = texto.split("h")

        horas = int(partes_h[0].strip())

        total_minutos += horas * 60

        # Dejamos solo la parte posterior a la "h"
        texto = partes_h[1]

    # Procesamos los minutos
    if "m" in texto:
        partes_m = texto.split("m")

        minutos = int(partes_m[0].strip())

        total_minutos += minutos

    elif texto.strip().isdigit():
        # Si quedó un número suelto, por ejemplo "30"
        total_minutos += int(texto.strip())

    return total_minutos


def listar(event = None):
    conn = sqlite3.connect('recetas.db')
    cursor = conn.execute(
                "SELECT COUNT(*) FROM RECETAS"
            )
    conn.text_factory = str
    conn.execute(
        "SELECT titulo, dificultad, unidades, tiempo FROM RECETAS"
    )
    resultados = cursor.fetchall()
    listar_recetas(resultados)
    conn.close()


def listar_recetas(cursor):

    v = Toplevel()
    v.title("Listado de recetas")

    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)

    lb = Listbox(
        v,
        width=150,
        yscrollcommand=sc.set
    )

    for row in cursor:

        s = 'TÍTULO: ' + str(row[0])

        lb.insert(END, s)

        lb.insert(
            END,
            "------------------------------------------------------------------------"
        )

        s = (
            "DIFICULTAD: " + str(row[1]) +
            " | UNIDADES: " + str(row[2]) +
            " | TIEMPO: " + str(row[2])
        )

        lb.insert(END, s)

        lb.insert(END, "")
        lb.insert(END, "")

    lb.pack(
        side=LEFT,
        fill=BOTH,
        expand=True
    )

    sc.config(command=lb.yview)
    
def buscar(elemento):

    v = Toplevel()
    v.geometry("400x100")

    if elemento == "autor":

        v.title("Buscar por autor")

        label = Label(
            v,
            text="Introduzca el autor:"
        )
        label.pack(side=LEFT)

        entry = Entry(v)
        entry.pack(side=LEFT)
        entry.focus()

        def realizar_busqueda(event=None):

            texto = entry.get()

            conn = sqlite3.connect("recetas.db")
            conn.text_factory = str

            cursor = conn.execute(
                """
                SELECT TITULO, DIFICULTAD, COMENSALES, TIEMPO
                FROM RECETAS
                WHERE AUTOR = ?
                """,
                (texto,)
            )

            resultados = cursor.fetchall()

            conn.close()

            listar_recetas(resultados)

        entry.bind("<Return>", realizar_busqueda)


    elif elemento == "fecha":

        v.title("Buscar por fecha")

        label = Label(
        v,
        text="Introduzca la fecha (dd/mm/aaaa):"
        )
        label.pack(side=LEFT)

        entry = Entry(v)
        entry.pack(side=LEFT)
        entry.focus()

    def realizar_busqueda(event=None):

        fecha = entry.get()

        try:
            # Convertimos dd/mm/aaaa a aaaa-mm-dd
            fecha_dt = datetime.strptime(
                fecha,
                "%d/%m/%Y"
            )

            fecha_sql = fecha_dt.strftime(
                "%Y-%m-%d"
            )

        except ValueError:
            messagebox.showerror(
                "Error",
                "La fecha debe tener el formato dd/mm/aaaa"
            )
            return

        conn = sqlite3.connect("recetas.db")
        conn.text_factory = str

        cursor = conn.execute(
            """
            SELECT TITULO, DIFICULTAD, COMENSALES, TIEMPO
            FROM RECETAS
            WHERE FECHA < ?
            """,
            (fecha_sql,)
        )

        resultados = cursor.fetchall()

        conn.close()

        listar_recetas(resultados)

        entry.bind("<Return>", realizar_busqueda)

    boton = Button(
        v,
        text="Buscar",
        command=realizar_busqueda
    )
    boton.pack(side=LEFT)

    
def ventana_principal():

    def listar():
        conn = sqlite3.connect("recetas.db")
        conn.text_factory = str

        cursor = conn.execute(
            """
            SELECT * FROM RECETAS
            """
        )

        resultados = cursor.fetchall()

        conn.close()

        listar_recetas(resultados)

    raiz = Tk()
    raiz.title("Gestión de recetas")
    raiz.geometry("500x300")

    menu = Menu(raiz)

    # -------------------------
    # MENÚ DATOS
    # -------------------------

    menudatos = Menu(
        menu,
        tearoff=0
    )

    menudatos.add_command(
        label="Cargar",
        command=cargar
    )

    menudatos.add_command(
        label="Salir",
        command=raiz.quit
    )

    menu.add_cascade(
        label="Datos",
        menu=menudatos
    )

    # -------------------------
    # MENÚ LISTAR
    # -------------------------

    menulistar = Menu(
        menu,
        tearoff=0
    )

    menulistar.add_command(
        label="Listar",
        command=listar
    )

    menu.add_cascade(
        label="Listar",
        menu=menulistar
    )

    # -------------------------
    # MENÚ BUSCAR
    # -------------------------

    menubuscar = Menu(
        menu,
        tearoff=0
    )

    menubuscar.add_command(
        label="Autor",
        command=lambda: buscar("autor")
    )

    menubuscar.add_command(
        label="Fecha",
        command=lambda: buscar("fecha")
    )

    menu.add_cascade(
        label="Buscar",
        menu=menubuscar
    )

    # -------------------------
    # MOSTRAR MENÚ
    # -------------------------

    raiz.config(menu=menu)

    raiz.mainloop()

if __name__ == "__main__":
    ventana_principal()