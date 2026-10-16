#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import *
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

    conn = sqlite3.connect('comics.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS COMICS")
    conn.execute('''CREATE TABLE COMICS
       (TITULO            TEXT NOT NULL,
        DISPONIBILIDAD    TEXT        ,
        PRECIO_ORIGINAL      DOUBLE,
        PRECIO_DESCUENTO DOUBLE,
        ENCUADERNACION TEXT,
        FECHA DATE,   
        COLECCION         TEXT
        );''')
    conn.execute("DROP TABLE IF EXISTS AUTORES")
    conn.execute('''CREATE TABLE AUTORES
           (TITULO            TEXT NOT NULL,
            AUTOR TEXT
            );''')
    
    url = "https://www.universal-comics.com/comics.html"
    f = urllib.request.urlopen(url, timeout=20)
    s = BeautifulSoup(f, 'lxml')
    lista_comics = s.find("div", class_ = "listado vista micro").ul.find_all("li")
    for elemento in lista_comics:
        enlace = elemento.div.div.div.a["href"]
        enlace = f"https://www.universal-comics.com{enlace}"
        web_comic = urllib.request.urlopen(enlace, timeout=20)
        s_comic = BeautifulSoup(web_comic, 'lxml')
        titulo = s_comic.find("div", class_ = "columna-de").div.find("h1", class_ = "titulo").get_text().strip()
        disponibilidad = s_comic.find("div", class_="panel").span.get_text().strip()
        precio_original = s_comic.find("div", class_ = "panel panel-precio").find("span", class_ = "precio-anterior").get_text().replace("€", "").strip()
        precio_descuento = s_comic.find("div", class_ = "panel panel-precio").find("span", class_ = "precio ofertado").get_text().replace("€", "").strip()
        encuadernacion = s_comic.find("li", class_ = "encuadernacion").find("span", class_ = "valor-propiedad").get_text().strip()
        fecha = s_comic.find("li", class_ = "fechaedicion").find("span", class_ = "valor-propiedad").get_text().strip()
        coleccion = s_comic.find("div", class_="panel-propiedades-producto").find("li", class_="coleccion").find("span", class_="valor-propiedad").get_text().strip()
        autores = s_comic.find("div", class_="panel-propiedades-producto").find("li", class_="autores").find("span", class_="valor-propiedad").get_text().strip()
        fecha_final = datetime.strptime(fecha, "%d/%m/%Y")
        lista_autores = autores.strip().split("-")
        for autor in lista_autores:
            autor = autor.strip()
            conn.execute("""INSERT INTO AUTORES (TITULO, AUTOR) VALUES (?,?)""",
                                    (titulo, autor))
            conn.commit()
        conn.execute("""INSERT INTO COMICS (TITULO, DISPONIBILIDAD, PRECIO_ORIGINAL, PRECIO_DESCUENTO, ENCUADERNACION, FECHA, COLECCION) VALUES (?,?,?,?,?,?,?)""",
                                              (titulo, disponibilidad, precio_original, precio_descuento, encuadernacion, fecha_final, coleccion))
        conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM COMICS")
    messagebox.showinfo("Base Datos",
                                                     "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()
    
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
        lb.insert(END,"Colección: " + row[7])
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
    cursor = conn.execute("SELECT * FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO ")
    imprimir_lista(cursor)
    conn.close()
    
def listar_comics_con_descuento():
    conn = sqlite3.connect('comics.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT * FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO  where PRECIO_DESCUENTO IS NOT NULL ORDER BY PRECIO_DESCUENTO DESC")
    imprimir_lista(cursor)
    conn.close()
    
def buscar_por_autor():
    def listar(event=None):
            conn = sqlite3.connect('comics.db')
            conn.text_factory = str
            autores = autor.get()
            cursor = conn.execute("SELECT * FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO where AUTOR = ?", (autores,))
            resultados = cursor.fetchall()
            conn.close()
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
                cursor = conn.execute("SELECT * FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO WHERE FECHA < ?", (fecha,))
                conn.close()
                imprimir_lista(cursor)
            except:
                conn.close()
                messagebox.showerror(title="Error",message="Error en la fecha\nFormato dd-mm-aaaa")  
    v = Toplevel()
    label = Label(v, text="Introduzca la fecha (dd-mm-aaaa) ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)
    
def buscar_por_titulo_o_coleccion():
    def listar(event=None):
            conn = sqlite3.connect('comics.db')
            conn.text_factory = str
            if (titulo):
                cursor = conn.execute("SELECT * FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO WHERE C.TITULO LIKE '%" + entry.get() + "%'")
                conn.close()
                imprimir_lista(cursor)
            elif (coleccion):
                cursor = conn.execute("SELECT * FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO WHERE C.COLECCION LIKE '%" + entry.get() + "%'")
                conn.close()
                imprimir_lista(cursor)
            else:
                cursor = conn.execute("SELECT * FROM COMICS C JOIN AUTORES A ON C.TITULO = A.TITULO WHERE C.COLECCION LIKE '%" + entry.get() + "%' OR C.TITULO LIKE '%" + entry.get() + "%'")
                conn.close()
                imprimir_lista(cursor)            
    
    v = Toplevel()
    v.title("Cómics por título o colección") 

    titulo = Checkbutton(v, text="Título", variable=BooleanVar()).pack(side=TOP)
    coleccion = Checkbutton(v, text="Colección", variable=BooleanVar()).pack(side=TOP)

    Label(v, text="Introduce una palabra:").pack(side=TOP)

    entry = Entry(v)
    entry.pack(side=TOP)
    entry.bind("<Return>", listar)

    Button(v, text="Buscar", command=listar).pack(side=TOP)
    
    
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