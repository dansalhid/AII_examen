#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime
# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context



def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_bd()

def almacenar_bd():

    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS PELICULAS")
    conn.execute('''CREATE TABLE PELICULAS
       (TITULO            TEXT NOT NULL,
        TITULO_ORIGINAL    TEXT        ,       
        FECHA         DATE,
        DIRECTOR TEXT
        );''')
    conn.execute("DROP TABLE IF EXISTS PAISES")
    conn.execute('''CREATE TABLE PAISES
           (TITULO            TEXT NOT NULL,
            PAIS TEXT
            );''')
    conn.execute("DROP TABLE IF EXISTS GENEROS")
    conn.execute('''CREATE TABLE GENEROS
               (TITULO            TEXT NOT NULL,
                GENERO TEXT
                );''')
    
    url = "https://www.elseptimoarte.net/estrenos/2025/"
    f = urllib.request.urlopen(url, timeout=20)
    s = BeautifulSoup(f, 'lxml')
    lista_peliculas = s.find("ul", class_ = "elements").find_all("li")
    for elemento in lista_peliculas:
        enlace = elemento.h3.a["href"]
        enlace = f"https://www.elseptimoarte.net{enlace}"
        web_pelicula = urllib.request.urlopen(enlace, timeout=20)
        s2 = BeautifulSoup(web_pelicula, 'lxml')
        datos = s2.find("section", class_ = "highlight").div.dl
        titulo = datos.find("dt", string= "Título").find_next_sibling().getText()
        titulo_original = datos.find("dt", string= "Título original").find_next_sibling().getText()
        paises = datos.find("dt", string= "País").find_next_sibling().find_all("a")
        fecha = datos.find("dt", string= "Estreno en España").find_next_sibling().getText().strip()
        fecha_final = datetime.strptime(fecha, "%d/%m/%Y")
        generos = s2.find("div", id= "datos_pelicula").find("p", class_ = "categorias").find_all("a")
        director = s2.find("div", id= "datos_pelicula").find("p", class_ = "director").span.a.span.get_text()
        print(director)
        for pais in paises:
            pais = pais.getText()
            print(pais)
            conn.execute("""INSERT INTO PAISES (TITULO, PAIS) VALUES (?,?)""",
                                                                  (titulo, pais))
            conn.commit()
        for genero in generos:
            genero = genero.get_text()
            conn.execute("""INSERT INTO GENEROS (TITULO, GENERO) VALUES (?,?)""",
                                                                              (titulo, genero))
            conn.commit()
        conn.execute("""INSERT INTO PELICULAS (TITULO, TITULO_ORIGINAL, FECHA, DIRECTOR) VALUES (?,?,?,?)""",
                                      (titulo, titulo_original, fecha_final, director))
        conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM PELICULAS")
    messagebox.showinfo("Base Datos",
                                             "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()

almacenar_bd()