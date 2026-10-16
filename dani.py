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

    url = f"https://www.universal-comics.com/comics.html"

    f = urllib.request.urlopen(url, timeout=20)
    s = BeautifulSoup(f, "lxml")

    for comic in s.find_all("div", class_="panel-informacion"):
        enlace = comic.find("a")["href"]
        url2 = f"https://www.universal-comics.com{enlace}"

        f2 = urllib.request.urlopen(url2, timeout=20)
        s2 = BeautifulSoup(f2, "lxml")
        
        titulo = s2.find("h1").text.strip()

        coleccion = s2.find("div", class_="panel-propiedades-producto").find("li", class_="coleccion").find("span", class_="valor-propiedad").text.strip()

        autores = s2.find("div", class_="panel-propiedades-producto").find("li", class_="autores").find("span", class_="valor-propiedad").text.strip()

        autores_lista = []
        for autor in autores.split("-"):
            autores_lista.append(autor.strip())

        print(titulo, autores_lista)

def obtener_descuento(precio_original, precio_descuento):
    return round((precio_original - precio_descuento) / precio_original * 100, 2)
