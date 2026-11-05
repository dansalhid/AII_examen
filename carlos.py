#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD, ID
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup

# lineas para evitar error SSL
import ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_datos()

def almacenar_datos():
    lista = []
    for i in range(1,3):
        url = f"https://zacatrus.es/juegos-de-mesa.html?p={i}"
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
        enlaces = s.find_all("li", class_ = "item product product-item")
        for juego in enlaces:
            enlace = juego.div.a['href']
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
                            enlace,
                            headers=cabeceras
                            )
            f2 = urllib.request.urlopen(peticion, timeout=20)
            s2 = BeautifulSoup(f2, 'lxml')
            titulo = s2.find("h1", class_ = "page-title").span.get_text()
            precio = s2.find("div", class_ = "club-badge-info")
            if precio is not None:
                precio = precio.find("span", class_ = "club-final-price").get_text()
            else:
                precio = s2.find("span", class_ = "price").get_text().replace("€", "").strip()
            complejidad = s2.find("div", attrs={"data-th": "Complejidad"})
            if complejidad is not None:
                complejidad = complejidad.get_text()
            tematicas = s2.find("div", attrs={"data-th": "Temática"})
            if tematicas is not None:
                tematicas = tematicas.get_text()
            num_jugadores = s2.find("div", attrs={"data-th": "Núm. jugadores"})
            if num_jugadores is not None:
                num_jugadores = num_jugadores.get_text()
                lista_jugadores = num_jugadores.strip().split(", ")
                if lista_jugadores[-1].__contains__("+"):
                    lista_jugadores[-1] = int(lista_jugadores[-1])+1
                    res = ""
                    for elemento in lista_jugadores:
                        res = res + str(elemento) + ", "
                    print(res[:-2].strip())
                    num_jugadores = res[:-2].strip()
            detalles = s2.find("div", class_ = "product attribute description").get_text()
            lista.append((titulo, precio, tematicas, complejidad, num_jugadores, detalles))
            
            
almacenar_datos()