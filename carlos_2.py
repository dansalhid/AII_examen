from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import date, datetime

import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context
    
def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_bd()

def almacenar_bd():

    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS PELICULAS")
    conn.execute('''CREATE TABLE PELICULAS
       (TITULO            TEXT NOT NULL,
        TITULO_ORIGINAL    TEXT        ,       
        FECHA         DATE,
        DIRECTOR TEXT
        );''')
    conn.execute("DROP TABLE IF EXISTS PAISES")
    conn.execute('''CREATE TABLE PAISES
           (TITULO            TEXT NOT NULL,
            PAIS TEXT
            );''')
    conn.execute("DROP TABLE IF EXISTS GENEROS")
    conn.execute('''CREATE TABLE GENEROS
               (TITULO            TEXT NOT NULL,
                GENERO TEXT
                );''')
    
    url = "https://www.elseptimoarte.net/estrenos/2025/"
    f = urllib.request.urlopen(url, timeout=20)
    s = BeautifulSoup(f, 'lxml')
    lista_peliculas = s.find("ul", class_ = "elements").find_all("li")
    for elemento in lista_peliculas:
        enlace = elemento.h3.a["href"]
        enlace = f"https://www.elseptimoarte.net{enlace}"
        web_pelicula = urllib.request.urlopen(enlace, timeout=20)
        s2 = BeautifulSoup(web_pelicula, 'lxml')
        datos = s2.find("section", class_ = "highlight").div.dl
        titulo = datos.find("dt", string= "Título").find_next_sibling().getText()
        titulo_original = datos.find("dt", string= "Título original").find_next_sibling().getText()
        paises = datos.find("dt", string= "País").find_next_sibling().find_all("a")
        fecha = datos.find("dt", string= "Estreno en España").find_next_sibling().getText().strip()
        fecha_final = datetime.strptime(fecha, "%d/%m/%Y")
        generos = s2.find("div", id= "datos_pelicula").find("p", class_ = "categorias").find_all("a")
        director = s2.find("div", id= "datos_pelicula").find("p", class_ = "director").span.a.span.get_text()
        print(director)
        for pais in paises:
            pais = pais.getText()
            print(pais)
            conn.execute("""INSERT INTO PAISES (TITULO, PAIS) VALUES (?,?)""",
                                                                  (titulo, pais))
            conn.commit()
        for genero in generos:
            genero = genero.get_text()
            conn.execute("""INSERT INTO GENEROS (TITULO, GENERO) VALUES (?,?)""",
                                                                              (titulo, genero))
            conn.commit()
        conn.execute("""INSERT INTO PELICULAS (TITULO, TITULO_ORIGINAL, FECHA, DIRECTOR) VALUES (?,?,?,?)""",
                                      (titulo, titulo_original, fecha_final, director))
        conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM PELICULAS")
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
        lb.insert(END,"Fecha: " + str(row[1]))
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
        lb.insert(END," País: "+ row[1] )
        lb.insert(END," Director: "+ row[2])
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
        lb.insert(END," País: "+ row[1] )
        lb.insert(END," Director: "+ row[2])
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
    
def listar_peliculas():
    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT PE.TITULO, P.PAIS, PE.DIRECTOR FROM PELICULAS PE JOIN PAIS P ON P.TITULO = PE.TITULO")
    imprimir_lista(cursor)
    conn.close()

def buscar_por_titulo():
    def listar(event):
            conn = sqlite3.connect('peliculas.db')
            conn.text_factory = str
            titulo = titulo.get()
            cursor = conn.execute("SELECT PE.TITULO, P.PAIS, PE.DIRECTOR FROM PELICULAS PE JOIN PAIS P ON P.TITULO = PE.TITULO where PE.TITULO = ?", (titulo,))
            resultados = cursor.fetchall()
            conn.close
            imprimir_lista_2(resultados)
            
    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT TITULO FROM PELICULAS WHERE TITULO IS NOT NULL")
    
    titulos = [i[0] for i in cursor]
    
    v = Toplevel()
    label = Label(v,text="Seleccione el titulo: ")
    label.pack(side=LEFT)
    titulo = Spinbox(v, width= 30, values=titulos, state='readonly')
    titulo.bind("<Return>", listar)
    titulo.pack(side=LEFT)
    
    conn.close()
    
def buscar_por_fecha():
    def listar(event):
            conn = sqlite3.connect('peliculas.db')
            conn.text_factory = str
            try:
                fecha = datetime.strptime(str(entry.get()),"%d-%m-%Y")
                cursor = conn.execute("SELECT TITULO, FECHA FROM PELICULAS WHERE FECHA > ?", (fecha,))
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
    
def buscar_por_genero():
    def listar(event):
            conn = sqlite3.connect('peliculas.db')
            conn.text_factory = str
            genero = genero.get()
            cursor = conn.execute("SELECT PE.TITULO, PE.FECHA FROM PELICULAS PE JOIN GENEROS P ON P.TITULO = PE.TITULO where P.GENERO = ?", (genero,))
            resultados = cursor.fetchall()
            conn.close
            imprimir_lista_2(resultados)
            
    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT GENERO FROM GENEROS WHERE TITULO IS NOT NULL")
    
    generos = [i[0] for i in cursor]
    
    v = Toplevel()
    label = Label(v,text="Seleccione el género: ")
    label.pack(side=LEFT)
    genero = Spinbox(v, width= 30, values=generos, state='readonly')
    genero.bind("<Return>", listar)
    genero.pack(side=LEFT)

def ventana_principal():
    def listar():
            conn = sqlite3.connect('peliculas.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT *  FROM RECETAS")
            conn.close
            listar_peliculas(cursor)
    
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menudatos.add_command(label="Listar", command=listar_peliculas)
    menu.add_cascade(label="Datos", menu=menudatos)
    
    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Peliculas por titulo", command=buscar_por_titulo)
    menubuscar.add_command(label="Peliculas por fecha", command=buscar_por_fecha)
    menubuscar.add_command(label="Peliculas por género", command=buscar_por_genero)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()



if __name__ == "__main__":
    ventana_principal()