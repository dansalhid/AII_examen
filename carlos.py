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
    
    url = "https://www.universal-comics.com/comics.html"
    f = urllib.request.urlopen(url, timeout=20)
    s = BeautifulSoup(f, 'lxml')
    lista_comics = s.find("div", class_ = "listado vista micro").ul.find_all("li")
    print(lista_comics)
    for elemento in lista_comics:
        enlace = elemento.div.div.div.a["href"]
        web_comic = urllib.request.urlopen(enlace, timeout=20)
        s_comic = BeautifulSoup(web_comic, 'lxml')
        
    

almacenar_bd()