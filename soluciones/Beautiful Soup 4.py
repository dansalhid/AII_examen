#encoding:utf-8

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
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12
}

def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_bd()

def almacenar_bd():

    # Cambiar nombre de la base de datos en cada ejercicio 
    conn = sqlite3.connect('libros.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS LIBROS")
    conn.execute('''CREATE TABLE LIBROS
       (TITULO            TEXT NOT NULL,
        PRECIO      DOUBLE,
        FECHA            DATE,          
        AUTOR         TEXT,
        URL        TEXT);''')
    conn.execute("DROP TABLE IF EXISTS GENEROS")
    conn.execute('''CREATE TABLE GENEROS
           (TITULO            TEXT NOT NULL,
            GENERO        TEXT);''')
    conn.execute("DROP TABLE IF EXISTS REDES")
    conn.execute('''CREATE TABLE REDES
               (AUTOR            TEXT NOT NULL,
               TWITTER        TEXT,
               FACEBOOK        TEXT);''')

    #camniar la url de la página web en cada ejercicio
    f = urllib.request.urlopen("https://editorialamarante.es/libros/narrativa")
    s = BeautifulSoup(f, "lxml")
    lista_libros = s.find("div", class_="book-list")
    for v in lista_libros.find_all("div", class_ = "media"):
        body = v.find("div", class_ = "media-body")
        enlace = body.h4.a["href"]
        titulo = body.h4.a.next_element.get_text()
        autor = body.find("div", class_ = "row").find("div", class_ = "col-md-4").p.a.next_element.get_text()
        fecha = body.find("div", class_ = "row").find("div", class_ = "col-md-4").p.text.strip().split("\n")[4]
        fecha_text = fecha.strip().split(":")[1].strip()
        fecha_lista = fecha_text.strip().split()
        mes = fecha_lista[0]
        anyo = fecha_lista[-1]
        mes_numero = meses.get(mes)
        fecha_final = date(int(anyo), mes_numero, 1)
        generos = body.find("div", class_ = "row").find("div", class_ = "col-md-4").p.text.strip().split("\n")[3]
        enlace_autor = body.find("div", class_ = "row").find("div", class_ = "col-md-4").p.a["href"]
        web_autor = urllib.request.urlopen(f'https://editorialamarante.es/{enlace_autor}')
        s_autor = BeautifulSoup(web_autor, "lxml")
        base = s_autor.find("div", class_ = "content-autores").find("div", class_ = "container").find("div",class_ = "row").div
        facebook = base.find("div", class_ = "social-sharing").find("a", class_ = "share-facebook")["href"]
        twitter = base.find("div", class_ = "social-sharing").find("a", class_ = "share-twitter")["href"]
        generos_sin_titulo = generos.strip().split(":")[1]
        lista_generos = generos_sin_titulo.strip().split(". ")
        f = urllib.request.urlopen(f'https://editorialamarante.es{enlace}')
        s = BeautifulSoup(f, "lxml")
        datos = s.find("div", class_ = "row").find("div", class_ = "col-sm-8").find("div", class_ = "row").find("div", class_ = "col-md-5").p.get_text()
        texto_precio = datos.strip().split("\n")[-1]
        precio_final = texto_precio.split(" ")[1]
        conn.execute("""INSERT INTO LIBROS (TITULO, PRECIO, FECHA, AUTOR, URL) VALUES (?,?,?,?,?)""",
                      (titulo, precio_final, fecha_final, autor, enlace))
        conn.commit()
        conn.execute("""INSERT INTO REDES (AUTOR, TWITTER, FACEBOOK) VALUES (?,?,?)""",
                              (autor, twitter, facebook))
        conn.commit()
        for genero in lista_generos:
            conn.execute("""INSERT INTO GENEROS (TITULO, GENERO) VALUES (?,?)""",
                                  (titulo, genero))
            conn.commit()
        
    cursor = conn.execute("SELECT COUNT(*) FROM REDES")
    messagebox.showinfo("Base Datos",
                             "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()


def buscar_mas_baratos():  
    def listar(event):
            conn = sqlite3.connect('libros.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT TITULO, AUTOR, PRECIO FROM LIBROS WHERE TITULO LIKE '%" + str(entry.get()) + "%'")
            conn.close
            listar_libros(cursor)
    ventana = Toplevel()
    label = Label(ventana, text="Introduzca cadena a buscar ")
    label.pack(side=LEFT)
    entry = Entry(ventana)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)

    

def buscar_por_fecha():
    def listar(event):
            conn = sqlite3.connect('libros.db')
            conn.text_factory = str
            try:
                fecha = datetime.strptime(str(entry.get()),"%d/%m/%Y")
                cursor = conn.execute("SELECT * FROM LIBROS WHERE FECHA > ?", (fecha,))
                conn.close
                listar_libros(cursor)
            except:
                conn.close
                messagebox.showerror(title="Error",message="Error en la fecha\nFormato dd7mm/aaaa")  
    v = Toplevel()
    label = Label(v, text="Introduzca la fecha (dd/mm/aaaa) ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)

def listar_todo():
    conn = sqlite3.connect('libros.db')
    conn.text_factory = str
    try:
        cursor = conn.execute("SELECT * FROM LIBROS")
        conn.close
        listar_libros(cursor)
    except:
        conn.close
        
def listar_baratos():
    conn = sqlite3.connect('libros.db')
    conn.text_factory = str
    try:
        cursor = conn.execute("SELECT * FROM LIBROS ORDER BY PRECIO ASC LIMIT 5")
        conn.close
        listar_libros(cursor)
    except:
        conn.close

def buscar_por_genero():

    def listar(event=None):
        conn = sqlite3.connect('libros.db')
        conn.text_factory = str

        genero = entry.get()

        cursor = conn.execute("""
            SELECT DISTINCT L.TITULO, L.PRECIO, L.FECHA, L.AUTOR, L.URL
            FROM LIBROS L
            JOIN GENEROS G ON L.TITULO = G.TITULO
            WHERE G.GENERO = ?
        """, (genero,))

        resultados = cursor.fetchall()
        conn.close()

        listar_libros(resultados)

    conn = sqlite3.connect('libros.db')
    conn.text_factory = str

    cursor = conn.execute("""
        SELECT DISTINCT GENERO
        FROM GENEROS
        ORDER BY GENERO
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
    
def buscar_por_autor():

    def listar(event=None):
        conn = sqlite3.connect('libros.db')
        conn.text_factory = str

        autor = entry.get()

        cursor = conn.execute("""
            SELECT * FROM REDES WHERE AUTOR = ?
        """, (autor,))

        resultados = cursor.fetchall()
        conn.close()

        listar_autores(resultados)

    conn = sqlite3.connect('libros.db')
    conn.text_factory = str

    cursor = conn.execute("""
        SELECT DISTINCT AUTOR
        FROM REDES
        ORDER BY AUTOR
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


def listar(event = None):
    conn = sqlite3.connect('libros.db')
    cursor = conn.execute(
                "SELECT COUNT(*) FROM LIBROS"
            )
    conn.text_factory = str
    conn.execute(
        "SELECT * FROM LIBROS"
    )
    resultados = cursor.fetchall()
    listar_libros(resultados)
    conn.close()

def listar_libros(cursor):

    v = Toplevel()
    v.title("Listado de libros")

    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)

    lb = Listbox(
        v,
        width=150,
        yscrollcommand=sc.set
    )

    for row in cursor:

        s = 'TÍTULO: ' + str(row[0])

        lb.insert(END, s)

        lb.insert(
            END,
            "------------------------------------------------------------------------"
        )

        s = (
            "1: " + str(row[1]) +
            " 2: " + str(row[2]) +
            " 3: " + str(row[3]) +
            " 4: " + str(row[4])
        )

        lb.insert(END, s)

        lb.insert(END, "")
        lb.insert(END, "")

    lb.pack(
        side=LEFT,
        fill=BOTH,
        expand=True
    )

    sc.config(command=lb.yview)
    
def listar_autores(cursor):

    v = Toplevel()
    v.title("Listado de autores")

    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)

    lb = Listbox(
        v,
        width=150,
        yscrollcommand=sc.set
    )

    for row in cursor:

        s = 'AUTOR: ' + str(row[0])

        lb.insert(END, s)

        lb.insert(
            END,
            "------------------------------------------------------------------------"
        )

        s = (
            "Twitter: " + str(row[1]) +
            " Facebook: " + str(row[2])
        )

        lb.insert(END, s)

        lb.insert(END, "")
        lb.insert(END, "")

    lb.pack(
        side=LEFT,
        fill=BOTH,
        expand=True
    )

    sc.config(command=lb.yview)



def ventana_principal():
    def listar():
            conn = sqlite3.connect('libros.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT * FROM LIBROS")
            conn.close
            listar_libros(cursor)
    
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)
    
    menulistar = Menu(menu, tearoff=0)
    menulistar.add_command(label="Libros", command=listar)
    menulistar.add_command(label="Barato", command=listar_baratos)
    menu.add_cascade(label="Listar", menu=menulistar)
    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Fecha", command=buscar_por_fecha)
    menubuscar.add_command(label="Autores", command=buscar_por_autor)
    menubuscar.add_command(label="Generos", command=buscar_por_genero)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()



if __name__ == "__main__":
    ventana_principal()