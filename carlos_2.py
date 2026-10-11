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
    
def imprimir_lista(cursor):
    v = Toplevel()
    v.title("LISTADO DE JUEGOS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"Título: " + row[0])
        lb.insert(END," Porcentaje_vp: "+ str(row[1]))
        lb.insert(END," Precio: "+ str(row[2]))
        lb.insert(END," Temáticas: "+ row[3] )
        lb.insert(END," Complejidad: "+ row[4] )
        lb.insert(END,"\n\n")
        lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)

def imprimir_lista_1(cursor):
    v = Toplevel()
    v.title("LISTADO DE JUEGOS POR TEMATICA")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"Título: " + row[0])
        lb.insert(END," Temáticas: "+ row[1] )
        lb.insert(END," Complejidad: "+ row[2] )
        lb.insert(END,"\n\n")
        lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)

def listar_juegos():
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT * FROM JUEGOS")
    imprimir_lista(cursor)
    conn.close()

def listar_mejores_juegos():
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT * FROM JUEGOS WHERE PORCENTAJE_VP >= 90 ORDER BY PORCENTAJE_VP ASCENDENT")
    imprimir_lista(cursor)
    conn.close()
    
def buscar_por_tematica(): 
    def listar(event):
        conn = sqlite3.connect('recetas.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT * FROM JUEGOS where TEMATICA LIKE '%" + tematica.get() + "%'")
        conn.close
        imprimir_lista_1(cursor,"tematica "+ tematica.get())
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT TEMATICA FROM JUEGOS")
    
    tematicas = [i[0] for i in cursor]
    
    v = Toplevel()
    label = Label(v,text="Seleccione el tematica: ")
    label.pack(side=LEFT)
    tematica = Spinbox(v, width= 30, values=tematicas, state='readonly')
    tematica.bind("<Return>", listar)
    tematica.pack(side=LEFT)
    
    conn.close()
    
def buscar_por_complejidad():
    def listar(event):
            conn = sqlite3.connect('recetas.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT * FROM JUEGOS where COMPLEJIDAD LIKE '%" + str(complejidad.get()) + "%'")
            conn.close
            imprimir_lista_1(cursor,"complejidad "+ complejidad.get())
            
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT COMPLEJIDAD FROM JUEGOS")
    
    complejidades = [i[0] for i in cursor]
    
    v = Toplevel()
    label = Label(v,text="Seleccione la complejidad: ")
    label.pack(side=LEFT)
    complejidad = Spinbox(v, width= 30, values=complejidades, state='readonly')
    complejidad.bind("<Return>", listar)
    complejidad.pack(side=LEFT)
    
    conn.close()

def ventana_principal():
    root = Tk()
    root.geometry("150x100")
    
    menubar = Menu(root)
    
    datosmenu = Menu(menubar, tearoff=0)
    datosmenu.add_command(label="Cargar", command=almacenar_bd)
    datosmenu.add_separator()
    datosmenu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datosmenu)
    
    listarmenu = Menu(menubar, tearoff=0)
    listarmenu.add_command(label="Juegos", command=listar_juegos)
    listarmenu.add_command(label="Mejores juegos", command=listar_mejores_juegos)
    
    menubar.add_cascade(label="Listar", menu=listarmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Juegos por temática", command=buscar_por_tematica)
    buscarmenu.add_command(label="Juegos por complejidad", command=buscar_por_complejidad)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
    
    root.config(menu=menubar)
    root.mainloop()
    
if __name__ == "__main__":
    ventana_principal()
