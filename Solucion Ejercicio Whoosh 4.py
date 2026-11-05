#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD, ID
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup

# lineas para evitar error SSL
import ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_datos()
  
 
def extraer_peliculas():
    #devuelve una lista de tuplas. Cada tupla tiene la información requerida de una pelicula
    lista_peliculas = []
        
    for i in range(1,4):
        lista_pagina = extraer_pelicula("https://www.elseptimoarte.net/estrenos/2024/"+str(i))
        lista_peliculas.extend(lista_pagina)
        
    return lista_peliculas 
    
#extrae todas las peliculas que hay en una página y devuelve una lista    
def extraer_pelicula(url):
    
    lista =[]
    
    f = urllib.request.urlopen(url)
    s = BeautifulSoup(f, "lxml")
    lista_link_peliculas = s.find("ul", class_="elements")
    if lista_link_peliculas: # por si no hay cuatro páginas
        lista_link_peliculas = s.find("ul", class_="elements").find_all("li")
    else:
        lista_link_peliculas = []
    for link_pelicula in lista_link_peliculas:
        url_detalle = link_pelicula.a['href']
        f = urllib.request.urlopen("https://www.elseptimoarte.net/"+url_detalle)
        s = BeautifulSoup(f, "lxml")
        aux = s.find("main", class_="informativo").find_all("section",class_="highlight")
        datos = aux[0].div.dl
        titulo_original = datos.find("dt",string="Título original").find_next_sibling("dd").string.strip()
        #si no tiene título se pone el título original
        if (datos.find("dt",string="Título")):
            titulo = datos.find("dt",string="Título").find_next_sibling("dd").string.strip()
        else:
            titulo = titulo_original      
        if(datos.find("dt",string="País")):
            pais = "".join(datos.find("dt",string="País").find_next_sibling("dd").stripped_strings)
        else:
            pais="Desconocido"
        fecha = datetime.strptime(datos.find("dt",string="Estreno en España").find_next_sibling("dd").string.strip(), '%d/%m/%Y')
        
        sinopsis = aux[1].div.text.strip()
        
        generos_director = s.find("div",id="datos_pelicula")
        generos = "".join(generos_director.find("p",class_="categorias").stripped_strings)
        director = "".join(generos_director.find("p",class_="director").stripped_strings)
           
        lista.append((titulo,titulo_original,pais,fecha,director,generos,sinopsis,url_detalle))
        
    return lista


#almacena cada pelicula en un documento de un índice. Usa la función extraer_peliculas() para obtener la lista de peliculas 
def almacenar_datos():
    
    #define el esquema de la información
    schem = Schema(titulo=TEXT(stored=True,phrase=False), titulo_original=TEXT(stored=True,phrase=False), pais=KEYWORD(stored=True,commas=True,lowercase=True), fecha=DATETIME(stored=True), director=KEYWORD(stored=True,commas=True,lowercase=True), generos=KEYWORD(stored=True,commas=True,lowercase=True), sinopsis=TEXT(stored=True,phrase=False), url=ID(stored=True,unique=True))
    
    #eliminamos el directorio del índice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    
    #creamos el índice
    ix = create_in("Index", schema=schem)
    #creamos un writer para poder añadir documentos al indice
    writer = ix.writer()
    i=0
    lista=extraer_peliculas()
    for pelicula in lista:
        #añade cada pelicula de la lista al índice
        writer.add_document(titulo=str(pelicula[0]), titulo_original=str(pelicula[1]), pais=str(pelicula[2]), fecha=pelicula[3], director=str(pelicula[4]), generos=str(pelicula[5]), sinopsis=str(pelicula[6]), url=str(pelicula[7]))    
        i+=1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " películas")          


# permite buscar palabras en el "titulo" o en la "sinopsis" de las peliculas 
def buscar_titulo_sinopsis():
    def mostrar_lista(event):
        #abrimos el índice
        ix=open_dir("Index")
        #creamos un searcher en el índice    
        with ix.searcher() as searcher:
            #se crea la consulta: buscamos en los campos "titulo" o "sinopsis" alguna de las palabras que hay en el Entry "en"
            #se usa la opción OrGroup para que use el operador OR por defecto entre palabras, en lugar de AND
            query = MultifieldParser(["titulo","sinopsis"], ix.schema, group=OrGroup).parse(str(en.get()))
            #llamamos a la función search del searcher, pasándole como parámetro la consulta creada
            results = searcher.search(query) #sólo devuelve los 10 primeros
            #recorremos los resultados obtenidos(es una lista de diccionarios) y mostramos lo solicitado
            v = Toplevel()
            v.title("Listado de Peliculas")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            #Importante: el diccionario solo contiene los campos que han sido almacenados(stored=True) en el Schema
            for r in results: 
                lb.insert(END,r['titulo'])
                lb.insert(END,r['titulo_original'])
                lb.insert(END,r['director'])
                lb.insert(END,'')
    
    v = Toplevel()
    v.title("Busqueda por Título o Sinopsis")
    l = Label(v, text="Introduzca las palabras a buscar:")
    l.pack(side=LEFT)
    en = Entry(v)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
        


# permite buscar las películas de un "género"
def buscar_generos():
    def mostrar_lista(event):
        ix=open_dir("Index")      
        with ix.searcher() as searcher:
            #lista de todos los géneros disponibles en el campo de géneros
            lista_generos = [i.decode('utf-8') for i in searcher.lexicon('generos')]
            # en la entrada ponemos todo en minúsculas
            entrada = str(en.get().lower())
            #si la entrada no está en la lista de géneros disponibles, da un error e informa de los géneros disponibles     
            if entrada not in lista_generos:
                messagebox.showinfo("Error", "El criterio de búsqueda no es un género existente\nLos géneros existentes son: " + ",".join(lista_generos))
                return
            
            query = QueryParser("generos", ix.schema).parse('"'+entrada+'"')
            results = searcher.search(query, limit=20) #sólo devuelve los 20 primeros
            v = Toplevel()
            v.title("Listado de Películas")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            for r in results:
                lb.insert(END,r['titulo'])
                lb.insert(END,r['titulo_original'])
                lb.insert(END,r['pais'])
                lb.insert(END,'')
    
    v = Toplevel()
    v.title("Busqueda por Género")
    l = Label(v, text="Introduzca género a buscar:")
    l.pack(side=LEFT)
    en = Entry(v)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

# permite buscar una película por su título y modificar su fecha de estreno
def modificar_fecha():
    def modificar():
        #comprobamos el formato de la entrada
        if(not re.match("\d{8}",en1.get())):
            messagebox.showinfo("Error", "Formato del rango de fecha incorrecto")
            return
        ix=open_dir("Index")
        lista=[]    # lista de las películas a modificar, usamos el campo url (unique) para updates 
        with ix.searcher() as searcher:
            query = QueryParser("titulo", ix.schema).parse(str(en.get()))
            results = searcher.search(query, limit=None) 
            v = Toplevel()
            v.title("Listado de Películas a Modificar")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            for r in results:
                lb.insert(END,r['titulo'])
                lb.insert(END,r['fecha'])
                lb.insert(END,'')
                lista.append(r) #cargamos la lista con los resultados de la búsqueda
        # actualizamos con la nueva fecha de estreno todas las películas de la lista
        respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere modificar las fechas de estrenos de estas peliculas?")
        if respuesta:
            writer = ix.writer()
            for r in lista:
                writer.update_document(url=r['url'], fecha=datetime.strptime(str(en1.get()),'%Y%m%d'), titulo=r['titulo'], titulo_original=r['titulo_original'], pais=r['pais'], director=r['director'], generos=r['generos'], sinopsis=r['sinopsis'])
            writer.commit()
    
    v = Toplevel()
    v.title("Modificar Fecha Estreno")
    l = Label(v, text="Introduzca Título Película:")
    l.pack(side=LEFT)
    en = Entry(v)
    en.pack(side=LEFT)
    l1 = Label(v, text="Introduzca Fecha Estreno AAAAMMDD:")
    l1.pack(side=LEFT)
    en1 = Entry(v)
    en1.pack(side=LEFT)
    bt = Button(v, text='Modificar', command=modificar)
    bt.pack(side=LEFT)

def buscar_fecha():
    def mostrar_lista(event):
        #comprobamos el formato de la entrada
        if(not re.match("\d{8}\s+\d{8}",en.get())):
            messagebox.showinfo("Error", "Formato del rango de fecha incorrecto")
            return
        ix=open_dir("Index")      
        with ix.searcher() as searcher:
            
            aux = en.get().split()
            rango_fecha = '['+ aux[0] + ' TO ' + aux[1] +']'
            query = QueryParser("fecha", ix.schema).parse(rango_fecha)
            results = searcher.search(query,limit=None) #devuelve todos los resultados
            v = Toplevel()
            v.title("Listado de Películas")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            for r in results:
                lb.insert(END,r['titulo'])
                lb.insert(END,r['fecha'])
                lb.insert(END,'')
    
    v = Toplevel()
    v.title("Busqueda por Fecha")
    l = Label(v, text="Introduzca rango de fechas AAAAMMDD AAAAMMDD:")
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
    buscarmenu.add_command(label="Título o Sinopsis", command=buscar_titulo_sinopsis)
    buscarmenu.add_command(label="Géneros", command=buscar_generos)
    buscarmenu.add_command(label="Fecha", command=buscar_fecha)
    buscarmenu.add_command(label="Modificar Fecha", command=modificar_fecha)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

    

if __name__ == "__main__":
    ventana_principal()