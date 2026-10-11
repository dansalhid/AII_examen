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



def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_bd()

def almacenar_bd():

    # Cambiar nombre de la base de datos en cada ejercicio 
    conn = sqlite3.connect('vinos.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS VINOS")
    conn.execute('''CREATE TABLE VINOS
       (NOMBRE            TEXT NOT NULL,
        PRECIO    DOUBLE        ,
        ORIGEN      TEXT,
        BODEGA            TEXT);''')
    conn.execute("DROP TABLE IF EXISTS UVAS")
    conn.execute('''CREATE TABLE UVAS
           (NOMBRE            TEXT NOT NULL,
            UVA TEXT);''')

    #camniar la url de la página web en cada ejercicio
    indices = [0,36,72]
    for i in indices:
        f = urllib.request.urlopen(f'https://www.vinissimus.com/es/vinos/tinto/?cursor={i}')
        s = BeautifulSoup(f, "lxml")
        lista_vinos = s.find("div", class_="product-list").find_all("div", class_ = "product-list-item")
        for v in lista_vinos:
            url = v.find("div", class_ = "info").find("div", class_ = "details").a["href"]
            web_vino = urllib.request.urlopen(f'https://www.vinissimus.com/{url}')
            s_vino = BeautifulSoup(web_vino, "lxml")
            titulo = s_vino.find("div", class_ = "product-title")
            nombre = titulo.h1.get_text()
            anyo = titulo.span.get_text()
            nombre_vino = nombre + anyo
            precio = s_vino.find("div", class_ = "pprice")
            if precio:
                precio = precio.find("p", class_ = "dto price large")
            if not precio:
                precio = s_vino.find("p", class_="price uniq large")
            precio = precio.get_text().strip().split(" ")[0]
            precio = float(precio.replace(",", "."))
            denominacion = s_vino.find("div", class_ = "region with-link").a["title"]
            bodega = s_vino.find("div", class_ = "cellar with-link").a.get_text()
            uvas = s_vino.find("div", class_ = "tags with-link").find_all("span")
            lista_uvas = []
            for uva in uvas:
                lista_uvas.append(uva.a.get_text())
            for elemento in lista_uvas:
                conn.execute("""INSERT INTO UVAS (NOMBRE, UVA) VALUES (?,?)""",
                      (nombre_vino, elemento))
                conn.commit()
            conn.execute("""INSERT INTO VINOS (NOMBRE, PRECIO, ORIGEN, BODEGA) VALUES (?,?,?,?)""",
                                  (nombre_vino, precio, denominacion, bodega))
            conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM VINOS")
    messagebox.showinfo("Base Datos",
                         "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()


def buscar_por_precio():
    def listar(event=None):
        try:
            precio_max = float(entry.get().replace(",", "."))

            conn = sqlite3.connect('vinos.db')
            conn.text_factory = str

            try:
                cursor = conn.execute(
                    "SELECT * FROM VINOS WHERE PRECIO < ?",
                    (precio_max,)
                )
                vinos = cursor.fetchall()
            finally:
                conn.close()

            listar_vinos(vinos)

        except ValueError:
            print("Introduce un precio válido")

    ventana = Toplevel()
    label = Label(ventana, text="Introduzca precio a buscar")
    label.pack(side=LEFT)

    entry = Entry(ventana)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)

    

# def buscar_por_fecha():
#     def listar(event):
#             conn = sqlite3.connect('peliculas.db')
#             conn.text_factory = str
#             try:
#                 fecha = datetime.strptime(str(entry.get()),"%d-%m-%Y")
#                 cursor = conn.execute("SELECT TITULO, FECHA FROM PELICULA WHERE FECHA > ?", (fecha,))
#                 conn.close
#                 listar_peliculas_1(cursor)
#             except:
#                 conn.close
#                 messagebox.showerror(title="Error",message="Error en la fecha\nFormato dd-mm-aaaa")  
#     v = Toplevel()
#     label = Label(v, text="Introduzca la fecha (dd-mm-aaaa) ")
#     label.pack(side=LEFT)
#     entry = Entry(v)
#     entry.bind("<Return>", listar)
#     entry.pack(side=LEFT)



def buscar_por_denominacion():

    def listar(event=None):
        conn = sqlite3.connect('vinos.db')
        conn.text_factory = str

        autor = entry.get()

        cursor = conn.execute("""
            SELECT * FROM VINOS WHERE ORIGEN = ?
        """, (autor,))

        resultados = cursor.fetchall()
        conn.close()

        listar_vinos(resultados)

    conn = sqlite3.connect('vinos.db')
    conn.text_factory = str

    cursor = conn.execute("""
        SELECT DISTINCT ORIGEN
        FROM VINOS
        ORDER BY ORIGEN
    """)

    autores = [fila[0] for fila in cursor.fetchall()]
    conn.close()

    v = Toplevel()
    v.title("Buscar por autor")

    label = Label(v, text="Seleccione un autor")
    label.pack(side=LEFT)

    entry = Spinbox(
        v,
        values= autores,
        state='readonly'
    )
    entry.pack(side=LEFT)

    entry.bind("<Return>", listar)
    

def buscar_todo():
    conn = sqlite3.connect("vinos.db")
    try:
        cursor = conn.execute("SELECT * FROM VINOS")
        vinos = cursor.fetchall()
    finally:
        conn.close()

    listar_vinos(vinos)

def buscar_por_genero():

    def listar(event=None):
        conn = sqlite3.connect('vinos.db')
        conn.text_factory = str

        genero = entry.get()

        cursor = conn.execute("""
            SELECT DISTINCT L.NOMBRE, L.PRECIO, L.ORIGEN, L.BODEGA
            FROM VINOS L
            INNER JOIN UVAS G ON L.NOMBRE = G.NOMBRE
            WHERE G.UVA = ?
        """, (genero,))

        resultados = cursor.fetchall()
        conn.close()

        listar_vinos(resultados)

    conn = sqlite3.connect('vinos.db')
    conn.text_factory = str

    cursor = conn.execute("""
        SELECT DISTINCT UVA
        FROM UVAS
        ORDER BY UVA
    """)

    generos = [fila[0] for fila in cursor.fetchall()]
    conn.close()

    v = Toplevel()
    v.title("Buscar por género")

    label = Label(v, text="Seleccione un género")
    label.pack(side=LEFT)

    entry = Spinbox(
        v,
        values=generos,
        state='readonly'
    )
    entry.pack(side=LEFT)

    entry.bind("<Return>", listar)
    
    
def listar_vinos(cursor):      
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in cursor:
        s = 'TÍTULO: ' + row[0]
        lb.insert(END, s)
        lb.insert(END, "------------------------------------------------------------------------")
        s = "     PAÍS: " + str(row[1]) + ' | DIRECTOR: ' + row[2]
        lb.insert(END, s)
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)



def ventana_principal():
    def listar():
            conn = sqlite3.connect('vinos.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT *  FROM PELICULA")
            conn.close
            listar_vinos(cursor)
    
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Listar", command=buscar_todo)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Denominacion", command=buscar_por_denominacion)
    menubuscar.add_command(label="Precio", command=buscar_por_precio)
    menubuscar.add_command(label="Uvas", command=buscar_por_genero)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()



if __name__ == "__main__":
    ventana_principal()