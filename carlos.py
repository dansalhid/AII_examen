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
    conn.execute("DROP TABLE IF EXISTS JUEGOS COMICS")
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