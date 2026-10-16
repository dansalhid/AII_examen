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
        NUMERO_COMENSALES      INTEGER,         
        TIEMPO_PREPARACION         INTEGER,
        AUTOR         TEXT,
        FECHA         TEXT
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

            conn.execute("""INSERT INTO RECETAS (TITULO, DIFICULTAD, NUMERO_COMENSALES, TIEMPO_PREPARACION, AUTOR, FECHA) VALUES (?,?,?,?,?,?)""",
                         (titulo, dificultad, comensales, tiempo_preparacion, autor, fecha))

            conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM RECETAS")
    messagebox.showinfo("Base Datos",
                                                                 "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()


def imprimir_lista_3(cursor):
    v = Toplevel()
    v.title("LISTADO DE RECETAS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"Título: " + row[0])
        lb.insert(END," Dificultad: "+ row[1] )
        lb.insert(END," Número de comensales: "+ str(row[2]))
        lb.insert(END," Tiempo de preparación: "+ str(row[3]) )
        if row[4]:
            try:
                fecha = datetime.strptime(
                    str(row[4]),
                    "%Y-%m-%d %H:%M:%S"
                )
                fecha_formateada = datetime.strftime(
                    fecha,
                    "%d/%m/%Y"
                )
                s = "FECHA DE ESTRENO: " + fecha_formateada
            except ValueError:
                s = "FECHA DE ESTRENO: " + str(row[4])
        else:
            s = "FECHA DE ESTRENO: No disponible"
        lb.insert(END, s)
        lb.insert(END,"\n\n")
        lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)

def imprimir_lista_2(cursor):
    v = Toplevel()
    v.title("LISTADO DE RECETAS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"Título: " + row[0])
        lb.insert(END," Dificultad: "+ row[1] )
        lb.insert(END," Número de comensales: "+ str(row[2]))
        lb.insert(END," Tiempo de preparación: "+ str(row[3]) )
        lb.insert(END," Autor: "+ row[4] )
        lb.insert(END,"\n\n")
        lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)

def imprimir_lista(cursor):
    v = Toplevel()
    v.title("LISTADO DE RECETAS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"Título: " + row[0])
        lb.insert(END," Dificultad: "+ row[1] )
        lb.insert(END," Número de comensales: "+ str(row[2]))
        lb.insert(END," Tiempo de preparación: "+ str(row[3]) )
        # lb.insert(END," Autor: "+ row[4] )
        # if row[5]:
        #     try:
        #         fecha = datetime.strptime(
        #             str(row[5]),
        #             "%Y-%m-%d %H:%M:%S"
        #         )
        #         fecha_formateada = datetime.strftime(
        #             fecha,
        #             "%d/%m/%Y"
        #         )
        #         s = "FECHA DE ESTRENO: " + fecha_formateada
        #     except ValueError:
        #         s = "FECHA DE ESTRENO: " + str(row[5])
        # else:
        #     s = "FECHA DE ESTRENO: No disponible"
        # lb.insert(END, s)
        lb.insert(END,"\n\n")
        lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)
    
def listar_recetas():
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT TITULO, DIFICULTAD, NUMERO_COMENSALES, TIEMPO_PREPARACION FROM RECETAS")
    imprimir_lista(cursor)
    conn.close()

def buscar_por_autor():
    def listar(event):
            conn = sqlite3.connect('recetas.db')
            conn.text_factory = str
            nombre = autor.get()
            cursor = conn.execute("SELECT TITULO, DIFICULTAD, NUMERO_COMENSALES, TIEMPO_PREPARACION, AUTOR FROM RECETAS where AUTOR = ?", (nombre,))
            resultados = cursor.fetchall()
            conn.close
            imprimir_lista_2(resultados)
            
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT AUTOR FROM RECETAS WHERE AUTOR IS NOT NULL")
    
    autores = [i[0] for i in cursor]
    
    v = Toplevel()
    label = Label(v,text="Seleccione el autor: ")
    label.pack(side=LEFT)
    autor = Spinbox(v, width= 30, values=autores, state='readonly')
    autor.bind("<Return>", listar)
    autor.pack(side=LEFT)
    
    conn.close()
    
def buscar_por_fecha():
    def listar(event):
            conn = sqlite3.connect('recetas.db')
            conn.text_factory = str
            try:
                fecha = datetime.strptime(str(entry.get()),"%d-%m-%Y")
                cursor = conn.execute("SELECT TITULO, DIFICULTAD, NUMERO_COMENSALES, TIEMPO_PREPARACION, FECHA FROM RECETAS WHERE FECHA < ?", (fecha,))
                conn.close
                imprimir_lista_3(cursor)
            except:
                conn.close
                messagebox.showerror(title="Error",message="Error en la fecha\nFormato dd-mm-aaaa")  
    v = Toplevel()
    label = Label(v, text="Introduzca la fecha (dd-mm-aaaa) ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)

def ventana_principal():
    def listar():
            conn = sqlite3.connect('recetas.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT *  FROM RECETAS")
            conn.close
            listar_recetas(cursor)
    
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)
    
    #LISTAR
    listarmenu = Menu(menu, tearoff=0)
    listarmenu.add_command(label="Recetas", command=listar_recetas)
    
    menu.add_cascade(label="Listar", menu=listarmenu)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Recetas por autor", command=buscar_por_autor)
    menubuscar.add_command(label="Recetas por fecha", command=buscar_por_fecha)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()



if __name__ == "__main__":
    ventana_principal()