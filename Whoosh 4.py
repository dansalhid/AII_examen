
# encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from datetime import datetime
from whoosh import query
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD
from whoosh.qparser import QueryParser

# Líneas para evitar error SSL
import ssl

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


# def cargar():
#     respuesta = messagebox.askyesno(
#         title="Confirmar",
#         message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta"
#     )
#     if respuesta:
#         almacenar_datos()


def extraer_pelis():

    indices = [1, 2, 3]
    datos = []

    for i in indices:

        url = f"https://www.elseptimoarte.net/estrenos/2024/{i}/"

        try:
            f = urllib.request.urlopen(url)
            s = BeautifulSoup(f, "lxml")

            lista = s.find("ul", class_="elements")

            if lista is None:
                continue

            enlaces = lista.find_all("li")

            for elemento in enlaces:

                if not elemento.h3 or not elemento.h3.a:
                    continue

                peli = elemento.h3.a['href']

                url_peli = f"https://www.elseptimoarte.net{peli}"

                f2 = urllib.request.urlopen(url_peli)
                s2 = BeautifulSoup(f2, "lxml")

                informativo = s2.find(
                    "main",
                    class_="informativo"
                )

                if informativo is None:
                    continue

                highlight = informativo.find(
                    "section",
                    class_="highlight"
                )

                if highlight is None:
                    continue

                datos_peli = highlight.find("dl")

                if datos_peli is None:
                    continue

                # Título original
                dt_titulo_original = datos_peli.find(
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

                # Sinopsis
                info = s2.find("div", class_="info")

                sinopsis = info.find_all("p") if info else []

                texto = ""

                for parrafo in sinopsis:
                    texto = texto + parrafo.get_text() + "\n"

                # Título
                dt_titulo = datos_peli.find(
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
                dt_pais = datos_peli.find(
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
                dt_fecha = datos_peli.find(
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
                generos_director = s2.find(
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

                # Guardar los datos de la película
                datos.append((
                    titulo,
                    titulo_original,
                    fecha,
                    pais,
                    generos,
                    director,
                    texto,
                    url_peli
                ))

                print(datos[-1])

        except Exception as e:
            print(f"Error al procesar {url}: {e}")

    return datos