#encoding:utf-8

from numpy import indices

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



def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_bd()

def almacenar_bd():

    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS JUEGOS")
    conn.execute('''CREATE TABLE JUEGOS
       (TITULO            TEXT NOT NULL,
        PORCENTAJE_VP    INTEGER        ,
        PRECIO      DOUBLE,         
        COMPLEJIDAD         TEXT
        );''')
    conn.execute("DROP TABLE IF EXISTS TEMATICA")
    conn.execute('''CREATE TABLE TEMATICA
           (TITULO            TEXT NOT NULL,
            TEMATICA TEXT
            );''')

    
    indices = [1, 2]

    for i in indices:
        url = f"https://zacatrus.es/juegos-de-mesa.html?p={i}"

        peticion = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/131.0.0.0 Safari/537.36"
            }
        )

        f = urllib.request.urlopen(peticion, timeout=20)
        s = BeautifulSoup(f, "lxml")

        lista_juegos = s.find_all("li", class_="item product product-item")

        for juego in lista_juegos:
            enlace = juego.find("a", class_="product-item-link")["href"]
            titulo = juego.find("a", class_="product-item-link").text.strip()

            if (juego.find("div", class_="rating-result")):
                porcentaje_vp = juego.find("div", class_="rating-result").text.strip().replace("%", "")
            else:
                porcentaje_vp = None

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

            conn.execute("""INSERT INTO JUEGOS (TITULO, PORCENTAJE_VP, PRECIO, COMPLEJIDAD) VALUES (?,?,?,?)""",
                        (titulo, porcentaje_vp, precio, complejidad))

            conn.execute("""INSERT INTO TEMATICA (TITULO, TEMATICA) VALUES (?,?)""",
                        (titulo, tematica))

            conn.commit()

    cursor = conn.execute("SELECT COUNT(*) FROM JUEGOS")
    messagebox.showinfo("Base Datos",
                                             "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()

def imprimir_lista(cursor):
    v = Toplevel()
    v.title("LISTADO DE JUEGOS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"Título: " + row[0])
        lb.insert(END," Porcentaje_vp: "+ str(row[1] if row[1]!=None else "desconocido"))
        lb.insert(END," Precio: "+ str(row[2]))
        lb.insert(END," Complejidad: "+ str(row[3]) )
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
        lb.insert(END," Complejidad: "+ str(row[2]) )
        lb.insert(END,"\n\n")
        lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)
    

def imprimir_lista_2(cursor):
    v = Toplevel()
    v.title("LISTADO DE JUEGOS POR COMPLEJIDAD")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"Título: " + row[0])
        lb.insert(END," Complejidad: "+ str(row[1]) )
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
    cursor = conn.execute("SELECT * FROM JUEGOS WHERE PORCENTAJE_VP >= 90 AND PORCENTAJE_VP IS NOT NULL ORDER BY PORCENTAJE_VP DESC")
    imprimir_lista(cursor)
    conn.close()
    
def buscar_por_tematica():

    def listar(event=None):
        conn = sqlite3.connect('juegos.db')
        conn.text_factory = str

        genero = entry.get()

        cursor = conn.execute("""
            SELECT DISTINCT L.TITULO, L.PRECIO, L.PORCENTAJE_VP, L.COMPLEJIDAD
            FROM JUEGOS L
            INNER JOIN TEMATICA G ON L.TITULO = G.TITULO
            WHERE G.TEMATICA = ?
        """, (genero,))

        resultados = cursor.fetchall()
        conn.close()

        imprimir_lista_1(resultados)

    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str

    cursor = conn.execute("""
        SELECT DISTINCT TEMATICA
        FROM TEMATICA
        ORDER BY TEMATICA
    """)

    generos = [fila[0] for fila in cursor.fetchall()]
    conn.close()

    v = Toplevel()
    v.title("Buscar por temática")

    label = Label(v, text="Seleccione una temática")
    label.pack(side=LEFT)

    entry = Spinbox(
        v,
        values=generos,
        state='readonly'
    )
    entry.pack(side=LEFT)

    entry.bind("<Return>", listar)
    
def buscar_por_complejidad():
    def listar(event):
            conn = sqlite3.connect('juegos.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT * FROM JUEGOS where COMPLEJIDAD LIKE '%" + str(complejidad.get()) + "%'")
            conn.close
            imprimir_lista_2(cursor)
            
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT COMPLEJIDAD FROM JUEGOS WHERE COMPLEJIDAD IS NOT NULL")
    
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
