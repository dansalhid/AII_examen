#encoding:utf-8

from numpy import indices

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

    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS JUEGOS")
    conn.execute('''CREATE TABLE JUEGOS
       (TITULO            TEXT NOT NULL,
        PORCENTAJE_VP    INTEGER        ,
        PRECIO      DOUBLE,
        TEMATICA           TEXT,          
        COMPLEJIDAD         TEXT
        );''')
    conn.execute("DROP TABLE IF EXISTS TEMATICA")
    conn.execute('''CREATE TABLE TEMATICA
           (TITULO            TEXT NOT NULL,
            TEMATICA TEXT
            );''')

    
    indices = [1, 2]

    for i in indices:
        url = f"https://zacatrus.es/juegos-de-mesa.html?p={i}"

        peticion = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/131.0.0.0 Safari/537.36"
            }
        )

        f = urllib.request.urlopen(peticion, timeout=20)
        s = BeautifulSoup(f, "lxml")

        lista_juegos = s.find_all("li", class_="item product product-item")

        for juego in lista_juegos:
            enlace = juego.find("a", class_="product-item-link")["href"]
            titulo = juego.find("a", class_="product-item-link").text.strip()

            if (juego.find("span", class_="club-final-price" )):
                precio = juego.find("span", class_="club-final-price").text.replace("€", "").strip()
            else:
                precio = juego.find("span", class_="price").text.replace("€", "").strip()

            print(precio)


almacenar_bd()