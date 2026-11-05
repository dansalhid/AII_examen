#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD, NUMERIC
from whoosh.qparser import QueryParser
from datetime import datetime
# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context



def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_datos()

def extraer_juegos():
    lista = []
    
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
        s = BeautifulSoup(f, "lxml")
        
        lista_juegos = s.find_all("li", class_="item product product-item")

        for juego in lista_juegos:
            enlace = juego.find("a", class_="product-item-link")["href"]
            titulo = juego.find("a", class_="product-item-link").text.strip()

            if (juego.find("span", class_="club-final-price" )):
                precio = juego.find("span", class_="club-final-price").text.replace("€", "").strip()
            else:
                precio = juego.find("span", class_="price").text.replace("€", "").strip()

            peticion2 = urllib.request.Request(
                enlace,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                    }
                )

            f2 = urllib.request.urlopen(peticion2, timeout=20)
            s2 = BeautifulSoup(f2, "lxml")
            
            if (s2.find("div", attrs={"data-th": "Temática"})):
                tematica = s2.find("div", attrs={"data-th": "Temática"}).text.strip()
            else:
                tematica = None

            if (s2.find("div", attrs={"data-th": "Complejidad"})):
                complejidad = s2.find("div", attrs={"data-th": "Complejidad"}).text.strip()
            else:
                complejidad = None

            if (s2.find("div", attrs={"data-th": "Núm. jugadores"})):
                numero_jugadores = s2.find("div", attrs={"data-th": "Núm. jugadores"}).text.strip()
                if (numero_jugadores.__contains__("+")):
                    numero_jugadores = numero_jugadores.replace(", +", "")[:-1].strip()
            else:
                numero_jugadores = None

            detalles = s2.find("div", class_="product attribute description").text.strip()

            lista.append((titulo, precio, tematica, complejidad, numero_jugadores, detalles))
    return lista
 
def almacenar_datos():
     #define el esquema de la información
     schem = Schema(titulo=TEXT(phrase=False, stored=True) , precio=NUMERIC(numtype=float, stored=True), tematica=TEXT(stored=True), complejidad=TEXT(phrase=False, stored=True), numero_jugadores=KEYWORD(stored=True, commas=True), detalles=TEXT(phrase=False, stored=True))
     
     #eliminamos el directorio del índice, si existe
     if os.path.exists("Index"):
         shutil.rmtree("Index")
     os.mkdir("Index")
     
     #creamos el índice
     ix = create_in("Index", schema=schem)
     #creamos un writer para poder añadir documentos al indice
     writer = ix.writer()
     i=0
     lista=extraer_juegos()
     for j in lista:
         #añade cada estreno de la lista al índice
         writer.add_document(titulo=str(j[0]), precio=float(j[1]), tematica=j[2], complejidad=str(j[3]), numero_jugadores=int(j[4]), detalles=str(j[5]))   
         i+=1
     writer.commit()
     messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " juegos")          