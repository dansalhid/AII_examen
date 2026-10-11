# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime
import os
import ssl


# Líneas para evitar error SSL
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def cargar():
    respuesta = messagebox.askyesno(
        title="Confirmar",
        message="¿Está seguro que quiere recargar los datos?\n"
                "Esta operación puede ser lenta."
    )

    if respuesta:
        almacenar_bd()


def almacenar_bd():
    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str

    # Borrar tabla si existe
    conn.execute("DROP TABLE IF EXISTS PELICULA")

    # Crear tabla
    conn.execute('''
        CREATE TABLE PELICULA (
            TITULO TEXT NOT NULL,
            TITULO_ORIGINAL TEXT,
            PAIS TEXT,
            FECHA DATE,
            DIRECTOR TEXT,
            GENEROS TEXT
        );
    ''')

    try:
        # Página de estrenos
        f = urllib.request.urlopen(
            "https://www.elseptimoarte.net/estrenos/2025/"
        )

        s = BeautifulSoup(f, "lxml")

        lista = s.find("ul", class_="elements")

        if lista is None:
            messagebox.showerror(
                "Error",
                "No se ha encontrado la lista de películas."
            )
            conn.close()
            return

        lista_link_peliculas = lista.find_all("li")

        for link_pelicula in lista_link_peliculas:

            if link_pelicula.a is None:
                continue

            try:
                url = "https://www.elseptimoarte.net/" + link_pelicula.a['href']

                f = urllib.request.urlopen(url)
                s = BeautifulSoup(f, "lxml")

                informativo = s.find("main", class_="informativo")

                if informativo is None:
                    continue

                highlight = informativo.find(
                    "section",
                    class_="highlight"
                )

                if highlight is None:
                    continue

                datos = highlight.div.dl

                if datos is None:
                    continue

                # Título original
                dt_titulo_original = datos.find(
                    "dt",
                    string="Título original"
                )

                if dt_titulo_original:
                    dd = dt_titulo_original.find_next_sibling("dd")

                    if dd:
                        titulo_original = dd.get_text(strip=True)
                    else:
                        titulo_original = ""
                else:
                    titulo_original = ""

                # Título
                dt_titulo = datos.find(
                    "dt",
                    string="Título"
                )

                if dt_titulo:
                    dd = dt_titulo.find_next_sibling("dd")

                    if dd:
                        titulo = dd.get_text(strip=True)
                    else:
                        titulo = titulo_original
                else:
                    titulo = titulo_original

                # País
                dt_pais = datos.find(
                    "dt",
                    string="País"
                )

                if dt_pais:
                    dd = dt_pais.find_next_sibling("dd")

                    if dd:
                        pais = "".join(dd.stripped_strings)
                    else:
                        pais = ""
                else:
                    pais = ""

                # Fecha
                dt_fecha = datos.find(
                    "dt",
                    string="Estreno en España"
                )

                fecha = None

                if dt_fecha:
                    dd = dt_fecha.find_next_sibling("dd")

                    if dd:
                        texto_fecha = dd.get_text(strip=True)

                        try:
                            fecha = datetime.strptime(
                                texto_fecha,
                                '%d/%m/%Y'
                            )
                        except ValueError:
                            fecha = None

                # Géneros y director
                generos_director = s.find(
                    "div",
                    id="datos_pelicula"
                )

                generos = ""
                director = ""

                if generos_director:

                    p_generos = generos_director.find(
                        "p",
                        class_="categorias"
                    )

                    if p_generos:
                        generos = "".join(
                            p_generos.stripped_strings
                        )

                    p_director = generos_director.find(
                        "p",
                        class_="director"
                    )

                    if p_director:
                        director = "".join(
                            p_director.stripped_strings
                        )

                # Insertar película
                conn.execute(
                    """
                    INSERT INTO PELICULA
                    (TITULO, TITULO_ORIGINAL, PAIS,
                     FECHA, DIRECTOR, GENEROS)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        titulo,
                        titulo_original,
                        pais,
                        fecha,
                        director,
                        generos
                    )
                )

            except Exception as e:
                print("Error procesando película:", e)
                continue

        conn.commit()

        cursor = conn.execute(
            "SELECT COUNT(*) FROM PELICULA"
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


def buscar_por_titulo():

    def listar(event=None):
        conn = sqlite3.connect('peliculas.db')
        conn.text_factory = str

        cursor = conn.execute(
            """
            SELECT TITULO, PAIS, DIRECTOR
            FROM PELICULA
            WHERE TITULO LIKE ?
            """,
            ('%' + entry.get() + '%',)
        )

        resultados = cursor.fetchall()
        conn.close()

        listar_peliculas(resultados)

    ventana = Toplevel()
    ventana.title("Buscar por título")

    label = Label(
        ventana,
        text="Introduzca cadena a buscar:"
    )
    label.pack(side=LEFT)

    entry = Entry(ventana)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)

    entry.focus()


def buscar_por_fecha():

    def listar(event=None):
        conn = sqlite3.connect('peliculas.db')
        conn.text_factory = str

        try:
            fecha = datetime.strptime(
                str(entry.get()),
                "%d-%m-%Y"
            )

            cursor = conn.execute(
                """
                SELECT TITULO, FECHA
                FROM PELICULA
                WHERE FECHA > ?
                """,
                (fecha,)
            )

            resultados = cursor.fetchall()
            conn.close()

            listar_peliculas_1(resultados)

        except ValueError:
            conn.close()

            messagebox.showerror(
                title="Error",
                message="Error en la fecha.\n"
                        "Formato: dd-mm-aaaa"
            )

    v = Toplevel()
    v.title("Buscar por fecha")

    label = Label(
        v,
        text="Introduzca la fecha (dd-mm-aaaa):"
    )
    label.pack(side=LEFT)

    entry = Entry(v)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)

    entry.focus()


def buscar_por_genero():

    def listar(event=None):
        conn = sqlite3.connect('peliculas.db')
        conn.text_factory = str

        cursor = conn.execute(
            """
            SELECT TITULO, FECHA
            FROM PELICULA
            WHERE GENEROS LIKE ?
            """,
            ('%' + entry.get() + '%',)
        )

        resultados = cursor.fetchall()
        conn.close()

        listar_peliculas_1(resultados)

    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str

    cursor = conn.execute(
        "SELECT GENEROS FROM PELICULA"
    )

    generos = set()

    for i in cursor:
        generos_pelicula = i[0].split(",")

        for genero in generos_pelicula:
            genero = genero.strip()

            if genero:
                generos.add(genero)

    conn.close()

    v = Toplevel()
    v.title("Buscar por género")

    label = Label(
        v,
        text="Seleccione un género:"
    )
    label.pack(side=LEFT)

    entry = Spinbox(
        v,
        values=sorted(list(generos)),
        state='readonly',
        width=30
    )

    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)

    entry.focus()


def listar_peliculas_1(cursor):

    v = Toplevel()
    v.title("Películas")

    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)

    lb = Listbox(
        v,
        width=150,
        yscrollcommand=sc.set
    )

    for row in cursor:

        titulo = 'TÍTULO: ' + str(row[0])

        lb.insert(END, titulo)

        lb.insert(
            END,
            "-----------------------------------------------------"
        )

        # SQLite devuelve la fecha como texto
        if row[1]:

            try:
                fecha = datetime.strptime(
                    str(row[1]),
                    "%Y-%m-%d %H:%M:%S"
                )

                fecha_formateada = datetime.strftime(
                    fecha,
                    "%d/%m/%Y"
                )

                s = "FECHA DE ESTRENO: " + fecha_formateada

            except ValueError:
                s = "FECHA DE ESTRENO: " + str(row[1])

        else:
            s = "FECHA DE ESTRENO: No disponible"

        lb.insert(END, s)
        lb.insert(END, "")
        lb.insert(END, "")

    lb.pack(
        side=LEFT,
        fill=BOTH,
        expand=True
    )

    sc.config(command=lb.yview)


def listar_peliculas(cursor):

    v = Toplevel()
    v.title("Listado de películas")

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
            "PAÍS: " + str(row[1]) +
            " | DIRECTOR: " + str(row[2])
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


def ventana_principal():

    def listar():

        conn = sqlite3.connect('peliculas.db')
        conn.text_factory = str

        cursor = conn.execute(
            """
            SELECT TITULO, PAIS, DIRECTOR
            FROM PELICULA
            """
        )

        resultados = cursor.fetchall()

        conn.close()

        listar_peliculas(resultados)

    raiz = Tk()
    raiz.title("Gestión de películas")
    raiz.geometry("500x300")

    menu = Menu(raiz)

    # DATOS
    menudatos = Menu(
        menu,
        tearoff=0
    )

    menudatos.add_command(
        label="Cargar",
        command=cargar
    )

    menudatos.add_command(
        label="Listar",
        command=listar
    )

    menudatos.add_command(
        label="Salir",
        command=raiz.quit
    )

    menu.add_cascade(
        label="Datos",
        menu=menudatos
    )

    # BUSCAR
    menubuscar = Menu(
        menu,
        tearoff=0
    )

    menubuscar.add_command(
        label="Título",
        command=buscar_por_titulo
    )

    menubuscar.add_command(
        label="Fecha",
        command=buscar_por_fecha
    )

    menubuscar.add_command(
        label="Géneros",
        command=buscar_por_genero
    )

    menu.add_cascade(
        label="Buscar",
        menu=menubuscar
    )

    raiz.config(menu=menu)

    raiz.mainloop()


if __name__ == "__main__":
    ventana_principal()