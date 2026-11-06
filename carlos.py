from bs4 import BeautifulSoup
import urllib.request
import re
from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup
import locale
locale.setlocale(locale.LC_TIME, "es_ES")

# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context
    
def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_datos()

def extraer_juegos():
    
    lista=[]
    
    for p in range(1,4):
        req = urllib.request.Request("https://donmeeple.com/juegos-mesa/page/"+str(p)+"/", headers={'User-Agent': 'Mozilla/5.0'})
        f = urllib.request.urlopen(req)
        s = BeautifulSoup(f, 'lxml')
        l = s.find_all('article')

        for i in l:
            titulo = i.find('h2', class_='entry-title').a.string.replace(" – Reseña","")
            sinopsis = i.find('div', class_='entry-content').p.string
            fecha = i.find('div', class_='post-info-date').string
            fecha2 = datetime.strptime(fecha, "%d %B, %Y")
            print(fecha2)
            enlace = i.find('h2', class_='entry-title').a['href']
            req = urllib.request.Request(enlace, headers={'User-Agent': 'Mozilla/5.0'})
            f1 = urllib.request.urlopen(req)
            s1 = BeautifulSoup(f1, 'lxml')
            generos = s1.table.find('td',string='Género:').find_next_sibling('td').stripped_strings
            generos = ",".join([str(e) for e in generos])
            editorial = s1.table.find('td',string='Editorial:').find_next_sibling('td').text
            precio = s1.table.find('td',string=re.compile('Precio recomendado')).find_next_sibling('td').a.string.replace("€","").replace(",",".")
            print(precio)

            lista.append((titulo,sinopsis,fecha2,generos,editorial,precio))
            

    return lista

def almacenar_datos():
    
    #define el esquema de la información
    schem = Schema(titulo=TEXT(stored=True,phrase=False),
                   sinopsis=TEXT(stored=True,phrase=False),
                   fecha=DATETIME(stored=True),
                   generos=KEYWORD(stored=True,commas=True,lowercase=True),
                   editorial=TEXT(stored=True,phrase=False),
                   precio=NUMERIC(stored=True,numtype=float))

    #eliminamos el directorio del índice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    
    #creamos el índice
    ix = create_in("Index", schema=schem)
    #creamos un writer para poder añadir documentos al indice
    writer = ix.writer()
    i=0
    lista=extraer_juegos()
    for juego in lista:
        #añade cada juego de la lista al índice
        writer.add_document(titulo=str(juego[0]), sinopsis=str(juego[1]), fecha=juego[2], generos=str(juego[3]), editorial=str(juego[4]), precio=float(juego[5]))    
        i+=1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " juegos")
    
def buscar_precio():
    def mostrar_lista(event):
        #comprobamos el formato de la entrada
        if not re.match(r"\d{2}\.\d{2}-\d{2}\.\d{2}", en.get()):
            messagebox.showinfo("Error", "Formato de precos incorrecto. Debe ser: 00.00-00.00")
            return
        ix=open_dir("Index")      
        with ix.searcher() as searcher:
            
            aux = en.get().split("-")
            rango_precio = '['+ aux[0] + ' TO ' + aux[1] +']'
            query = QueryParser("precio", ix.schema).parse(rango_precio)
            results = searcher.search(query,limit=None) #devuelve todos los resultados
            v = Toplevel()
            v.title("Listado de Juegos por Precio")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            for r in results:
                lb.insert(END,r['titulo'])
                lb.insert(END,r['precio'])
                lb.insert(END,'')
    
    v = Toplevel()
    v.title("Busqueda por Precio")
    l = Label(v, text="Introduzca rango de precios 00.00-00.00:")
    l.pack(side=LEFT)
    en = Entry(v)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

def ventana_principal():
        
    root = Tk()
    menubar = Menu(root)
    
    datosmenu = Menu(menubar, tearoff=0)
    datosmenu.add_command(label="Cargar", command=cargar)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datosmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    # buscarmenu.add_command(label="Editorial", command=buscar_titulo_sinopsis)
    buscarmenu.add_command(label="Rango de precios", command=buscar_precio)
    # buscarmenu.add_command(label="Género y Título", command=buscar_fecha)
    # buscarmenu.add_command(label="Eliminar por fecha", command=modificar_fecha)
    # buscarmenu.add_command(label="Sinopsis y Precio más bajo", command=modificar_fecha)
    # buscarmenu.add_command(label="Título o Sinopsis", command=modificar_fecha)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

    

if __name__ == "__main__":
    ventana_principal()