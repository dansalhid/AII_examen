#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, DATETIME, NUMERIC, ID
from whoosh.qparser import QueryParser, MultifieldParser
from datetime import datetime
from whoosh import qparser, index, query


# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def cargar():
    if index.exists_in("Index"):
        respuesta = messagebox.askyesno(title="Confirmar",message="EL ÍNDICE YA EXISTE. \nEsta seguro que quiere recargar los datos?. \nEsta operación puede ser lenta")
        if respuesta:
            almacenar_datos()
    else:
        almacenar_datos()
            
 
        
def extraer_recetas():
    import locale #para activar las fechas en formato español
    locale.setlocale(locale.LC_TIME, "es_ES")
    
    lista=[]
    f = urllib.request.urlopen("https://www.recetasgratis.net/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html")
    s = BeautifulSoup(f,"lxml")
    l= s.find_all("div", class_=['resultado','link'])
    for i in l:
        titulo = i.a.string.strip()
        comensales = i.find("span",class_="comensales")
        if comensales:
            comensales = int(comensales.string.strip())
        else:
            comensales=-1
        
        f1 = urllib.request.urlopen(i.find('a')['href'])
        s1 = BeautifulSoup(f1,"lxml")
        autor = s1.find("div", class_='nombre_autor').a.string.strip()
        fecha = s1.find("div", class_='nombre_autor').find('span', class_="date_publish").string
        fecha = fecha.replace('Actualizado:','').strip()
        fecha = datetime.strptime(fecha, "%d %B %Y")
        introduccion = s1.find("div", class_="intro").text
        caracteristicas = s1.find("div", class_="properties inline")
        if caracteristicas:
            caracteristicas = caracteristicas.text.replace("Características adicionales:","")
            caracteristicas = ",".join([c.strip() for c in caracteristicas.split(",")] )     
        else:
            caracteristicas = "sin definir"
        lista.append((titulo, comensales, autor, fecha, caracteristicas,introduccion))
    
    return lista
 
def almacenar_datos():
    #define el esquema de la información
    schem = Schema(titulo=TEXT(stored=True), comensales=NUMERIC(stored=True, numtype=int), autor=ID(stored=True), fecha=DATETIME(stored=True), caracteristicas=KEYWORD(stored=True,commas=True) ,introduccion=TEXT(stored=True))
    
    #eliminamos el directorio del índice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    
    #creamos el índice
    ix = create_in("Index", schema=schem)
    #creamos un writer para poder añadir documentos al indice
    writer = ix.writer()
    i=0
    lista=extraer_recetas()
    for j in lista:
        #añade cada juego de la lista al índice
        writer.add_document(titulo=str(j[0]), comensales=int(j[1]), autor=str(j[2]), fecha=j[3], caracteristicas=str(j[4]), introduccion=str(j[5]))    
        i+=1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " recetas")          


def imprimir_lista(cursor):
    v = Toplevel()
    v.title("RECETAS DE COCINA DE RECETAS GRATIS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row['titulo'])
        if row['comensales'] > 0:
            lb.insert(END,"    Comensales: "+ str(row['comensales']))
        else:
            lb.insert(END,"    Comensales: "+ " sin definir")
        lb.insert(END,"    Autor: "+ row['autor'])
        lb.insert(END,"    Fecha: "+ datetime.strftime(row['fecha'],"%d/%m/%Y"))
        lb.insert(END,"    Caracteristicas: "+ row['caracteristicas'])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)
    
def imprimir_lista_1(cursor):
    v = Toplevel()
    v.title("RECETAS DE COCINA DE RECETAS GRATIS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row['titulo'])
        lb.insert(END,"    Introducción: "+ row['introduccion'])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)


def buscar_titulo_o_introduccion():
    def mostrar_lista(event):
        ix=open_dir("Index")   
        with ix.searcher() as searcher:
            query = MultifieldParser(["titulo","introduccion"], ix.schema).parse('"'+ str(en.get()) + '"')
            results = searcher.search(query,limit=3)
            imprimir_lista_1(results)
    
    v = Toplevel()
    v.title("Búsqueda por Título o Introducción")
        
    l1 = Label(v, text="Escriba frase del título o introducción:")
    l1.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)


def buscar_fecha():
    def mostrar_lista(event):
        ix=open_dir("Index")
        s = re.compile('(\d{2})/(\d{2})/(\d{4})\s+(\d{2})/(\d{2})/(\d{4})').match(str(en.get()))
        if s:
            fecha_i = s.group(3)+s.group(2)+s.group(1)
            fecha_f = s.group(6)+s.group(5)+s.group(4)
            with ix.searcher() as searcher:
                query = QueryParser("fecha", ix.schema).parse('['+fecha_i+' TO '+fecha_f+']')
                results = searcher.search(query,limit=None)
                imprimir_lista(results)
        else:
            messagebox.showerror("ERROR", "formato de rango de fechas incorrecto DD/MM/AAAA DD/MM/AAAA")
    
    v = Toplevel()
    v.title("Búsqueda por Fecha")
    l = Label(v, text="Introduzca el rango de fechas (DD/MM/AAAA DD/MM/AAAA):")
    l.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

    

def buscar_caracteristicas_y_titulo():
    def mostrar_lista():    
        with ix.searcher() as searcher:
            entrada = '"'+str(en.get())+'"' #se ponen comillas porque hay categorías con más de una palabra
            query = QueryParser("titulo", ix.schema).parse('caracteristicas:'+ entrada +' '+str(en1.get()))
            results = searcher.search(query,limit=10)
            imprimir_lista(results)
    
    v = Toplevel()
    v.title("Búsqueda por caracteristicas y Título")
    l = Label(v, text="Seleccione característica a buscar:")
    l.pack(side=LEFT)
    
    ix=open_dir("Index")      
    with ix.searcher() as searcher:
        #lista de todas las categorias disponibles en el campo de caracteristicas
        lista_caracteristicas = [i.decode('utf-8') for i in searcher.lexicon('caracteristicas')]
    
    en = Spinbox(v, values=lista_caracteristicas, state="readonly")
    en.pack(side=LEFT)
    
    l1 = Label(v, text="Escriba palabras del título:")
    l1.pack(side=LEFT)
    en1 = Entry(v, width=75)
    en1.pack(side=LEFT)
    
    b =Button(v, text="Buscar", command=mostrar_lista)
    b.pack(side=LEFT)

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
    datosmenu.add_command(label="Listar", command=listar_todo)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datosmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Título o Introducción", command=buscar_titulo_o_introduccion)
    buscarmenu.add_command(label="Fecha", command=buscar_fecha)
    buscarmenu.add_command(label="Caracteristicas y Título", command=buscar_caracteristicas_y_titulo)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

    

if __name__ == "__main__":
    ventana_principal()
