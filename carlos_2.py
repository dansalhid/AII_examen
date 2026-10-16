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
    
def imprimir_lista(cursor):
    v = Toplevel()
    v.title("LISTADO DE CÓMICS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"Título: " + row[0])
        lb.insert(END," Disponibilidad: "+ row[1] )
        lb.insert(END," Precio original: "+ str(row[2]))
        lb.insert(END," Precio con descuento: "+ str(row[3]))
        lb.insert(END," Encuadernación: "+ row[4] )
        s = "FECHA DE ESTRENO: " + str(row[5])
        lb.insert(END, s)
        lb.insert(END,"Autor: " + row[6])
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




def listar_comics():
    conn = sqlite3.connect('comics.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT C, A FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO ")
    imprimir_lista(cursor)
    conn.close()
    
def listar_comics_con_descuento():
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT C, A FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO  where PRECIO_DESCUENTO IS NOT NULL ORDER BY PRECIO_DESCUENTO DESC")
    imprimir_lista(cursor)
    conn.close()
    
def buscar_por_autor():
    def listar(event=None):
            conn = sqlite3.connect('comics.db')
            conn.text_factory = str
            autores = autor.get()
            cursor = conn.execute("SELECT C, A FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO where AUTOR = ?", (autores,))
            resultados = cursor.fetchall()
            conn.close
            imprimir_lista(resultados)
            
    conn = sqlite3.connect('comics.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT AUTOR FROM AUTORES WHERE AUTOR IS NOT NULL")
    
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
            conn = sqlite3.connect('comics.db')
            conn.text_factory = str
            try:
                fecha = datetime.strptime(str(entry.get()),"%d-%m-%Y")
                cursor = conn.execute("SELECT C, A FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO WHERE FECHA < ?", (fecha,))
                conn.close
                imprimir_lista(cursor)
            except:
                conn.close
                messagebox.showerror(title="Error",message="Error en la fecha\nFormato dd-mm-aaaa")  
    v = Toplevel()
    label = Label(v, text="Introduzca la fecha (dd-mm-aaaa) ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)
    
def buscar_por_titulo_o_coleccion():
    def listar(event):
            conn = sqlite3.connect('comics.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT * FROM COMICS")
            conn.close
            listar_comics(cursor)
    
    
def ventana_principal():
    def listar():
            conn = sqlite3.connect('comics.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT * FROM COMICS")
            conn.close
            listar_comics(cursor)
    
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)
    
    #LISTAR
    menulistar = Menu(menu, tearoff=0)
    menulistar.add_command(label="Todos los cómics", command=listar_comics)
    menulistar.add_command(label="Cómics con más descuentos", command=listar_comics_con_descuento)
    menu.add_cascade(label="Listar", menu=menulistar)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Cómics por autor", command=buscar_por_autor)
    menubuscar.add_command(label="Cómics por fecha", command=buscar_por_fecha)
    menubuscar.add_command(label="Comics por ơtulo o colección", command=buscar_por_titulo_o_coleccion)
    
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()
    
if __name__ == "__main__":
    ventana_principal()