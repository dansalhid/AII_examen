#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import *
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

    conn = sqlite3.connect('comics.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS COMICS")
    conn.execute('''CREATE TABLE COMICS
       (TITULO            TEXT NOT NULL,
        DISPONIBILIDAD    TEXT        ,
        PRECIO_ORIGINAL      DOUBLE,
        PRECIO_DESCUENTO DOUBLE,
        ENCUADERNACION TEXT,
        FECHA DATE,   
        COLECCION         TEXT
        );''')
    conn.execute("DROP TABLE IF EXISTS AUTORES")
    conn.execute('''CREATE TABLE AUTORES
           (TITULO            TEXT NOT NULL,
            AUTOR TEXT
            );''')
    
    url = "https://www.universal-comics.com/comics.html"
    f = urllib.request.urlopen(url, timeout=20)
    s = BeautifulSoup(f, 'lxml')
    lista_comics = s.find("div", class_ = "listado vista micro").ul.find_all("li")
    for elemento in lista_comics:
        enlace = elemento.div.div.div.a["href"]
        enlace = f"https://www.universal-comics.com{enlace}"
        web_comic = urllib.request.urlopen(enlace, timeout=20)
        s_comic = BeautifulSoup(web_comic, 'lxml')
        titulo = s_comic.find("div", class_ = "columna-de").div.find("h1", class_ = "titulo").get_text().strip()
        disponibilidad = s_comic.find("div", class_="panel").span.get_text().strip()
        precio_original = s_comic.find("div", class_ = "panel panel-precio").find("span", class_ = "precio-anterior").get_text().replace("€", "").strip()
        precio_descuento = s_comic.find("div", class_ = "panel panel-precio").find("span", class_ = "precio ofertado").get_text().replace("€", "").strip()
        encuadernacion = s_comic.find("li", class_ = "encuadernacion").find("span", class_ = "valor-propiedad").get_text().strip()
        fecha = s_comic.find("li", class_ = "fechaedicion").find("span", class_ = "valor-propiedad").get_text().strip()
        coleccion = s_comic.find("div", class_="panel-propiedades-producto").find("li", class_="coleccion").find("span", class_="valor-propiedad").get_text().strip()
        autores = s_comic.find("div", class_="panel-propiedades-producto").find("li", class_="autores").find("span", class_="valor-propiedad").get_text().strip()
        fecha_final = datetime.strptime(fecha, "%d/%m/%Y")
        lista_autores = autores.strip().split("-")
        for autor in lista_autores:
            autor = autor.strip()
            conn.execute("""INSERT INTO AUTORES (TITULO, AUTOR) VALUES (?,?)""",
                                    (titulo, autor))
            conn.commit()
        conn.execute("""INSERT INTO COMICS (TITULO, DISPONIBILIDAD, PRECIO_ORIGINAL, PRECIO_DESCUENTO, ENCUADERNACION, FECHA, COLECCION) VALUES (?,?,?,?,?,?,?)""",
                                              (titulo, disponibilidad, precio_original, precio_descuento, encuadernacion, fecha_final, coleccion))
        conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM COMICS")
    messagebox.showinfo("Base Datos",
                                                     "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()
    