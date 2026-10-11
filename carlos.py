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

    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS JUEGOS")
    conn.execute('''CREATE TABLE JUEGOS
       (TITULO            TEXT NOT NULL,
        PORCENTAJE_VP    DOUBLE        ,
        PRECIO      DOUBLE,
        TEMATICA           TEXT,          
        COMPLEJIDAD         TEXT
        );''')
    conn.execute("DROP TABLE IF EXISTS TEMATICA")
    conn.execute('''CREATE TABLE TEMATICA
           (TITULO            TEXT NOT NULL,
            TEMATICA TEXT
            );''')

    
    elementos = [1, 2]

    for i in elementos:
        url = f'https://zacatrus.es/juegos-de-mesa.html?p={i}'

        cabeceras = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/131.0.0.0 Safari/537.36'
        ),
        'Accept': (
            'text/html,application/xhtml+xml,'
            'application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        ),
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
        }

        peticion = urllib.request.Request(
        url,
        headers=cabeceras
        )

        f = urllib.request.urlopen(peticion, timeout=20)
        s = BeautifulSoup(f, 'lxml')
        lista = s.find_all("li", class_ = "item product product-item")
        for juego in lista:
            enlace = juego.find("div", class_ = "product-item-info").a["href"]
            print(enlace)
            peticion2 = urllib.request.Request(
                    enlace,
                    headers=cabeceras
                    )
            web_juego = urllib.request.urlopen(peticion2, timeout=20)
            s_juego = BeautifulSoup(web_juego, 'lxml')
            nombre = s_juego.find("h1", class_ = "page-title").span.get_text()
            porcentaje = s_juego.find("div", class_ = "rating-result")
            if not porcentaje:
                porcentaje = 50
            if porcentaje:
                porcentaje = porcentaje.span.get_text()
            print(porcentaje)
            

almacenar_bd()