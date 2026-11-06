
# encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, DATETIME, NUMERIC, ID
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import NumericRange
from datetime import datetime
from whoosh import qparser, index, query

# Líneas para evitar error SSL
import ssl

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_datos()

def extraer_juegos():
    lista = []
    
    elementos = [1, 2]

    for i in elementos:
        url = f'https://zacatrus.es/juegos-de-mesa.html?p={i}'

        cabeceras = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/131.0.0.0 Safari/537.36'
        ),
        'Accept': (
            'text/html,application/xhtml+xml,'
            'application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        ),
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
        }

        peticion = urllib.request.Request(
        url,
        headers=cabeceras
        )

        f = urllib.request.urlopen(peticion, timeout=20)
        s = BeautifulSoup(f, "lxml")
        
        lista_juegos = s.find_all("li", class_="item product product-item")

        for juego in lista_juegos:
            enlace = juego.find("a", class_="product-item-link")["href"]
            titulo = juego.find("a", class_="product-item-link").text.strip()

            if (juego.find("span", class_="club-final-price" )):
                precio = juego.find("span", class_="club-final-price").text.replace("€", "").replace(",", ".").strip();
            else:
                precio = juego.find("span", class_="price").text.replace("€", "").replace(",", ".").strip();
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

            if (s2.find("div", attrs={"data-th": "Núm. jugadores"})):
                numero_jugadores = s2.find("div", attrs={"data-th": "Núm. jugadores"}).text.strip()
                if (numero_jugadores.__contains__("+")):
                    numero_jugadores = numero_jugadores.replace(", +", "")[:-1].strip()
            else:
                numero_jugadores = None

            detalles = s2.find("div", class_="product attribute description").text.strip()

            lista.append((titulo, precio, tematica, complejidad, numero_jugadores, detalles))
    return lista
 
def almacenar_datos():
     #define el esquema de la información
     schem = Schema(titulo=TEXT(phrase=False, stored=True) , precio=NUMERIC(numtype=float, stored=True), tematica=TEXT(stored=True), complejidad=TEXT(phrase=False, stored=True), numero_jugadores=KEYWORD(stored=True, commas=True), detalles=TEXT(phrase=False, stored=True))
     
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
     for j in lista:
         #añade cada estreno de la lista al índice
         writer.add_document(titulo=str(j[0]), precio=float(j[1]), tematica=str(j[2]), complejidad=str(j[3]), numero_jugadores=str(j[4]), detalles=str(j[5]))   
         i+=1
     writer.commit()
     messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " juegos")          

def imprimir_lista(cursor):
    v = Toplevel()
    v.title("RECETAS DE COCINA DE RECETAS GRATIS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row['titulo'])
        lb.insert(END,row['precio'])
        lb.insert(END,row['tematica'])
        lb.insert(END,row['complejidad'])
        lb.insert(END,row['numero_jugadores'])
        lb.insert(END,row['detalles'])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)
    
def buscar_generos():
    def mostrar_lista(event):
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            entrada = en.get().strip().lower()
            query = QueryParser("generos", ix.schema).parse('"'+entrada+'"')
            results = searcher.search(query,limit=20)
            if len(results) == 0:
                messagebox.showerror(title="Error",message="¿Qué es Vinland?")   
            else:
                imprimir_lista(results)           
                
    v = Toplevel()
    v.title("Búsqueda por Título o Introducción")
        
    l1 = Label(v, text="Escriba frase del título o introducción:")
    l1.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    
def buscar_detalles():
    def mostrar_lista(event):
        ix=open_dir("Index")   
        with ix.searcher() as searcher:
            query = QueryParser("detalles", ix.schema).parse('"'+ str(en.get()) + '"')
            results = searcher.search(query,limit=10)
            imprimir_lista(results)

    v = Toplevel()
    v.title("Búsqueda por Título o Introducción")
        
    l1 = Label(v, text="Escriba frase de los detalles")
    l1.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

def buscar_tematicas():
    def mostrar_lista():    
        with ix.searcher() as searcher:
            entrada = '"'+str(en.get())+'"' #se ponen comillas porque hay categorías con más de una palabra
            query = QueryParser("tematicas", ix.schema).parse(entrada)
            results = searcher.search(query,limit=10)
            imprimir_lista(results)
    
    v = Toplevel()
    v.title("Búsqueda por caracteristicas y Título")
    l = Label(v, text="Seleccione característica a buscar:")
    l.pack(side=LEFT)
    
    ix=open_dir("Index")      
    with ix.searcher() as searcher:
        #lista de todas las categorias disponibles en el campo de caracteristicas
        lista_caracteristicas = [i.decode('utf-8') for i in searcher.lexicon('tematicas')]
    
    en = Spinbox(v, values=lista_caracteristicas, state="readonly")
    en.pack(side=LEFT)
 
    b =Button(v, text="Buscar", command=mostrar_lista)
    b.pack(side=LEFT)
    
def buscar_precio():
    def mostrar_lista(event):
        ix=open_dir("Index")   
        with ix.searcher() as searcher:
            query = NumericRange("precio", None, float(en.get()), endexcl=True)
            results = searcher.search(query,limit=10)
            imprimir_lista(results)

    v = Toplevel()
    v.title("Búsqueda por Título o Introducción")
        
    l1 = Label(v, text="Escriba frase de los detalles")
    l1.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    
def buscar_jugadores():
    def mostrar_lista(event):
        ix=open_dir("Index")   
        with ix.searcher() as searcher:
            query = QueryParser("jugadores", ix.schema).parse(str(en.get()))
            results = searcher.search(query,limit=10)
            imprimir_lista(results)

    v = Toplevel()
    v.title("Búsqueda por Título o Introducción")
        
    l1 = Label(v, text="Escriba frase de los detalles")
    l1.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

def ventana_principal():
    def listar_todo():
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            results = searcher.search(query.Every(),limit=None)
            imprimir_lista(results)
          
    root = Tk()
    root.geometry("150x100")

    menubar = Menu(root)
    
    datosmenu = Menu(menubar, tearoff=0)
    datosmenu.add_command(label="Cargar", command=cargar)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datosmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Detalles", command=buscar_detalles)
    buscarmenu.add_command(label="Temáticas", command=buscar_tematicas)
    buscarmenu.add_command(label="Precio", command=buscar_precio)
    buscarmenu.add_command(label="Jugadores", command=buscar_jugadores)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

    

if __name__ == "__main__":
    ventana_principal()