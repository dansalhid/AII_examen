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
    
    lista=[]
    
    for p in range(1,4):
        req = urllib.request.Request("https://donmeeple.com/juegos-mesa/page/"+str(p)+"/", headers={'User-Agent': 'Mozilla/5.0'})
        f = urllib.request.urlopen(req)
        s = BeautifulSoup(f, 'lxml')
        l = s.find_all('article')

        for i in l:
            titulo = i.find('h2', class_='entry-title').a.string.replace(" – Reseña","")
            sinopsis = i.find('div', class_='entry-content').p.string
            fecha = i.find('div', class_='post-info-date').string
            enlace = i.find('h2', class_='entry-title').a['href']
            req = urllib.request.Request(enlace, headers={'User-Agent': 'Mozilla/5.0'})
            f1 = urllib.request.urlopen(req)
            s1 = BeautifulSoup(f1, 'lxml')
            generos = s1.table.find('td',string='Género:').find_next_sibling('td').stripped_strings
            generos = ",".join([str(e) for e in generos])
            editorial = s1.table.find('td',string='Editorial:').find_next_sibling('td').text
            precio = s1.table.find('td',string=re.compile('Precio recomendado')).find_next_sibling('td').a.string.replace("€","")

            lista.append((titulo,sinopsis,fecha,generos,editorial,precio))

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

