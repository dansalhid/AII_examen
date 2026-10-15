#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime
from datetime import date

import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

meses = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12
}

def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_bd()

def almacenar_bd():

    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS RECETAS")
    conn.execute('''CREATE TABLE RECETAS
       (TITULO            TEXT NOT NULL,
        DIFICULTAD    TEXT        ,
        NUMERO_COMENSALES      INTEGER,        
        TIEMPO_PREPARACION INTEGER,
        AUTOR TEXT,
        FECHA DATETIME
        );''')
    
    url = "https://recetas.elperiodico.com/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
    f = urllib.request.urlopen(url, timeout=20)
    s = BeautifulSoup(f, 'lxml')
    enlaces = s.find_all("div", class_ = "resultado link")
    for e in enlaces:
        link = e.a['href']
        f2 = urllib.request.urlopen(link, timeout=20)
        s2 = BeautifulSoup(f2, 'lxml')
        datos = s2.find("div", class_ = "recipe-info")
        if datos is not None:
            comensales = datos.find("div", class_ = "properties").find("span", class_ = "property unidades")
            if comensales == None:
                comensales = datos.find("div", class_ = "properties").find("span", class_ = "property comensales")
            comensales = comensales.get_text().strip().split(" ")[0]
            duracion = datos.find("div", class_ = "properties").find("span", class_ = "property duracion").get_text()
            duracion = duracion.strip().split(" ")
            if len(duracion) == 1:
                duracion = duracion[0]
                if duracion.__contains__("m"):
                    duracion = int(duracion.replace("m", ""))
                else:
                    duracion = int(duracion.replace("h", ""))*60
            else:
                duracion = int(duracion[0].replace("h", ""))*60 + int(duracion[1].replace("m", ""))
            titulo = s2.find("h1", class_ = "titulo titulo--articulo").get_text()
            autor = s2.find("div", class_ = "nombre_autor").a.get_text()
            fecha = s2.find("div", class_ = "nombre_autor").span.get_text().strip().split(" ")
            if len(fecha) > 3:
                fecha.pop(0)
            dia = fecha[0]
            mes = meses.get(fecha[1])
            anyo = fecha[2]
            fecha_final = date(int(anyo), mes, int(dia))
            dificultad = datos.find("div", class_ = "properties").find("span", class_ = "property dificultad").get_text().replace("Dificultad", "")
            print(dificultad)
            conn.execute("""INSERT INTO RECETAS (TITULO, DIFICULTAD, NUMERO_COMENSALES, TIEMPO_PREPARACION, AUTOR, FECHA) VALUES (?,?,?,?,?,?)""",
                                              (titulo, dificultad, comensales, duracion, autor, fecha_final))
            conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM JUEGOS")
    messagebox.showinfo("Base Datos",
                                                     "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()
            
        


almacenar_bd()