#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from datetime import datetime
from whoosh import query
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD
from whoosh.qparser import QueryParser
from datetime import datetime


# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_datos()
        
def extraer_noticias():
    lista=[]
    
    f = urllib.request.urlopen("https://www.elseptimoarte.net/estrenos/2025")
    s = BeautifulSoup(f,"lxml")
    lista_link_peliculas = s.find("ul", class_="elements").find_all("li")
    for link_pelicula in lista_link_peliculas:
        f = urllib.request.urlopen("https://www.elseptimoarte.net/"+link_pelicula.a['href'].replace('î','i'))
        #el replace es poqrque hay un carácter no ascii en la url de una película
        s = BeautifulSoup(f,"lxml")
        datos = s.find("main", class_="informativo").find("section",class_="highlight").div.dl
        titulo_original = datos.find("dt",string="Título original").find_next_sibling("dd").string.strip()
        #si no tiene título se pone el título original
        if (datos.find("dt",string="Título")):
            titulo = datos.find("dt",string="Título").find_next_sibling("dd").string.strip()
        else:
            titulo = titulo_original      
        #pais = "".join(datos.find("dt",string="País").find_next_sibling("dd").stripped_strings)
        fecha = datetime.strptime(datos.find("dt",string="Estreno en España").find_next_sibling("dd").string.strip(), '%d/%m/%Y')
        
        generos_director = s.find("div",id="datos_pelicula")
        #generos = "".join(generos_director.find("p",class_="categorias").stripped_strings)
        director = "".join(generos_director.find("p",class_="director").stripped_strings)   
        
        
        sinopsis = s.find("div", class_="info", itemprop='description').text.strip()
                              
        lista.append((titulo, director, fecha, sinopsis))

    return lista


def imprimir_lista(cursor):
    
    v = Toplevel()
    v.title("ESTRENOS DE CINE")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row['titulo'])
        lb.insert(END,"    Director: "+ str(row['director']))
        lb.insert(END,"    Fecha: "+ datetime.strftime(row['fecha'], "%d/%m/%Y"))
        lb.insert(END,"    Sinopsis: "+ str(row['sinopsis'][0:99])+' ...')
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)

 
def almacenar_datos():
    #define el esquema de la información
    schem = Schema(titulo=TEXT(phrase=False, stored=True) , director=KEYWORD(stored=True, commas=True), fecha=DATETIME(stored=True), sinopsis=TEXT(phrase=False, stored=True))
    
    #eliminamos el directorio del índice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    
    #creamos el índice
    ix = create_in("Index", schema=schem)
    #creamos un writer para poder añadir documentos al indice
    writer = ix.writer()
    i=0
    lista=extraer_noticias()
    for j in lista:
        #añade cada estreno de la lista al índice
        writer.add_document(titulo=str(j[0]), director=str(j[1]), fecha=j[2], sinopsis=str(j[3]))    
        i+=1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " noticias")          


def buscar_director():
    def mostrar_lista(event):    
        with ix.searcher() as searcher:
            entrada = '"'+str(en.get().strip())+'"'
            query = QueryParser("director", ix.schema).parse(entrada)
            results = searcher.search(query,limit=None)
            imprimir_lista(results)
    
    
    v = Toplevel()
    v.title("Búsqueda por Director")
    l = Label(v, text="Seleccione director a buscar:")
    l.pack(side=LEFT)
    
    ix=open_dir("Index")      
    with ix.searcher() as searcher:
        #lista de todas los directores
        lista_autores = [i.decode('utf-8') for i in searcher.lexicon('director')]
    
    en = Spinbox(v, values=lista_autores, state="readonly")
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)


def buscar_fecha_y_titulo():
    def mostrar_lista():
        ix=open_dir("Index")   
        with ix.searcher() as searcher:
            s = re.compile('\d{8}').match(str(en.get()))
            if s:
                query = QueryParser("titulo", ix.schema).parse('fecha:' + str(en.get()) +' '+ str(en1.get()))
                results = searcher.search(query,limit=None)
                imprimir_lista(results)
            else:
                messagebox.showerror("ERROR", "formato de fecha incorrecto AAAAMMDD")
    
    v = Toplevel()
    v.title("Búsqueda por Fecha y Título")
    l = Label(v, text="Escriba una fecha (AAAAMMDD):")
    l.pack(side=LEFT)   
    en = Entry(v)
    en.pack(side=LEFT)
    
    l1 = Label(v, text="Escriba palabras del título:")
    l1.pack(side=LEFT)
    en1 = Entry(v, width=75)
    en1.pack(side=LEFT)
    
    b =Button(v, text="Buscar", command=mostrar_lista)
    b.pack(side=LEFT)
    
    
def eliminar_por_sinopsis():
    def modificar(event):
        ix=open_dir("Index") 
        with ix.searcher() as searcher:
            query = QueryParser("sinopsis", ix.schema).parse(str(en.get()))
            results = searcher.search(query, limit=None)
            if len(results) > 0: # si hay algún documento a borrar 
                v = Toplevel()
                v.title("Listado de Estrenos a Borrar")
                v.geometry('800x150')
                sc = Scrollbar(v)
                sc.pack(side=RIGHT, fill=Y)
                lb = Listbox(v, yscrollcommand=sc.set)
                lb.pack(side=BOTTOM, fill = BOTH)
                sc.config(command = lb.yview)
                for r in results:
                    lb.insert(END,r['titulo'])
                    lb.insert(END,'')
                # pedimos confirmación
                respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere eliminar estos estrenos?")
                if respuesta:
                    writer = ix.writer()
                    writer.delete_by_query(query)
                    writer.commit()
            else:
                messagebox.showinfo("AVISO", "No hay ningun estreno con esas palabras en la sinopsis")

    v = Toplevel()
    v.title("Eliminar Estrenos por Sinopsis")
    l = Label(v, text="Introduzca palabras en la sinopsis:")
    l.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", modificar)
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
    datosmenu.add_command(label="Cargar", command=almacenar_datos)
    datosmenu.add_command(label="Listar", command=listar_todo)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datosmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Director", command=buscar_director)
    buscarmenu.add_command(label="Fecha y Título", command=buscar_fecha_y_titulo)
    buscarmenu.add_command(label="Eliminar por Sinopsis", command=eliminar_por_sinopsis)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

    

if __name__ == "__main__":
    ventana_principal()