from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime

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
    cursor = conn.execute("SELECT TITULO, DIFICULTAD, N_COMENSALES, TIEMPO FROM RECETA")
    imprimir_lista(cursor)
    conn.close()

def buscar_por_autor():
    def listar(event):
            conn = sqlite3.connect('recetas.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT TITULO, DIFICULTAD, N_COMENSALES, TIEMPO, AUTOR FROM RECETA where AUTOR = ?")
            resultados = cursor.fetchall()
            conn.close
            imprimir_lista_2(resultados)
            
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT AUTOR FROM RECETA WHERE AUTOR IS NOT NULL")
    
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
                cursor = conn.execute("SELECT TITULO, DIFICULTAD, N_COMENSALES, TIEMPO, FECHA FROM RECETA WHERE FECHA < ?", (fecha,))
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
            cursor = conn.execute("SELECT *  FROM RECETA")
            conn.close
            listar_recetas(cursor)
    
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Listar", command=listar_recetas)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Recetas por autor", command=buscar_por_autor)
    menubuscar.add_command(label="Recetas por fecha", command=buscar_por_fecha)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()



if __name__ == "__main__":
    ventana_principal()