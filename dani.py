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
    conn.execute("DROP TABLE IF EXISTS PELICULA")
    conn.execute('''CREATE TABLE PELICULA
       (TITULO            TEXT NOT NULL,
        PORCENTAJE_VP    DOUBLE        ,
        PRECIO      DOUBLE,
        TEMATICA           TEXT,          
        COMPLEJIDAD         TEXT,
        ;''')

    
    f = urllib.request.urlopen("https://zacatrus.es/juegos-de-mesa.html ")
    s = BeautifulSoup(f, "lxml")