#encoding:utf-8

from numpy import indices

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime
from datetime import date
# lineas para evitar error SSL
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
        DIFICULTAD      TEXT,
        COMENSALES      INTEGER,         
        TIEMPO_PREPARACION         INTEGER,
        AUTOR         TEXT,
        FECHA_ACTUALIZACION         TEXT
        );''')


    url = f"https://recetas.elperiodico.com/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"

    peticion = urllib.request.Request(url)

    f = urllib.request.urlopen(peticion, timeout=20)
    s = BeautifulSoup(f, "lxml")

    for receta in s.find_all("div", class_="resultado link"):
        titulo = receta.find("a").text.strip()
        #if (titulo.startswith("Receta de")):
        enlace = receta.find("a")["href"]

        f2 = urllib.request.urlopen(enlace, timeout=20)
        s2 = BeautifulSoup(f2, "lxml")

        dificultad = None
        comensales = None
        tiempo_preparacion = None
        autor = None
        fecha_actualizacion = None
        if (s2.find("div", class_="properties")):
            dificultad = s2.find("div", class_="properties").find("span", class_="property dificultad").text.replace("Dificultad", "").strip()

            if (s2.find("div", class_="properties").find("span", class_="property unidades")):
                comensales = s2.find("div", class_="properties").find("span", class_="property unidades").text.replace("unidades", "").strip()
            else:
                comensales = s2.find("div", class_="properties").find("span", class_="property comensales").text.replace("comensales", "").strip()

            tiempo_preparacion = s2.find("div", class_="properties").find("span", class_="property duracion").text.strip()
            tiempo_preparacion_horas = 0
            tiempo_preparacion_minutos = 0
            if (tiempo_preparacion.__contains__("h")):
                tiempo_preparacion_horas = int(tiempo_preparacion.split("h")[0].strip()) * 60
            if (tiempo_preparacion.__contains__("m")):
                if (tiempo_preparacion.__contains__("h")):
                    tiempo_preparacion_minutos = int(tiempo_preparacion.split("h")[1].replace("m", "").strip())
                else:
                    tiempo_preparacion_minutos = int(tiempo_preparacion.replace("m", "").strip())

            tiempo_preparacion = tiempo_preparacion_horas + tiempo_preparacion_minutos
            autor = s2.find("div", class_="nombre_autor").find("a").text.strip()
            
            fecha_actualizacion = s2.find("span", class_="date_publish").text.strip()
            fecha_actualizacion_lista = fecha_actualizacion.split(" ")
            if len(fecha_actualizacion_lista) > 3:
                fecha_actualizacion_lista.pop(0)

            dia = fecha_actualizacion_lista[0]
            mes = meses.get(fecha_actualizacion_lista[1])
            año = fecha_actualizacion_lista[2]
            fecha = date(int(año), mes, int(dia))
            print(titulo)

            conn.execute("""INSERT INTO RECETAS (TITULO, DIFICULTAD, COMENSALES, TIEMPO_PREPARACION, AUTOR, FECHA_ACTUALIZACION) VALUES (?,?,?,?,?,?)""",
                         (titulo, dificultad, comensales, tiempo_preparacion, autor, fecha))

            conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM JUEGOS")
    messagebox.showinfo("Base Datos",
                                                                 "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()

        