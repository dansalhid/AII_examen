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
from whoosh.query import DateRange, NumericRange
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

#apartado a.
def buscar_editorial():
    def mostrar_lista():    
        with ix.searcher() as searcher:
            entrada = '"'+str(en.get())+'"' #se ponen comillas porque hay categorías con más de una palabra
            query = QueryParser("editorial", ix.schema).parse(entrada)
            results = searcher.search(query,limit=15)
            v = Toplevel()
            v.title("Listado de juegos")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            #Importante: el diccionario solo contiene los campos que han sido almacenados(stored=True) en el Schema
            for r in results: 
                lb.insert(END,r['titulo'])
                lb.insert(END,r['fecha'])
                lb.insert(END,r['generos'])
                lb.insert(END,r['editorial'])
                lb.insert(END,r['precio'])
                lb.insert(END,'')
    
    v = Toplevel()
    v.title("Búsqueda por caracteristicas y Título")
    l = Label(v, text="Seleccione característica a buscar:")
    l.pack(side=LEFT)
    
    ix=open_dir("Index")      
    with ix.searcher() as searcher:
        #lista de todas las categorias disponibles en el campo de caracteristicas
        lista_caracteristicas = [i.decode('utf-8') for i in searcher.lexicon('editorial')]
    
    en = Spinbox(v, values=lista_caracteristicas, state="readonly")
    en.pack(side=LEFT)
 
    b =Button(v, text="Buscar", command=mostrar_lista)
    b.pack(side=LEFT)
    
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
    

def eliminar_por_fecha():
    def modificar(event):
        if not re.fullmatch(r"\d{2}-\d{2}-\d{4}-\d{2}-\d{2}-\d{4}", en.get()):
            messagebox.showinfo(
                "Error",
                "Formato de fechas incorrecto. Debe ser: DD-MM-AAAA-DD-MM-AAAA"
            )
            return
        aux = en.get().split("-")
        fecha_inicial = "-".join(aux[0:3])
        fecha_final = "-".join(aux[3:6])
        fecha_inicial = datetime.strptime(fecha_inicial, "%d-%m-%Y")
        fecha_final = datetime.strptime(fecha_final, "%d-%m-%Y")
        ix = open_dir("Index")
        with ix.searcher() as searcher:
            query = DateRange("fecha",fecha_inicial, datetime.combine(fecha_final.date(), datetime.max.time()), startexcl=False, endexcl=False)
            results = searcher.search(query, limit=None)

            if len(results) > 0:
                v = Toplevel()
                v.title("Listado de Estrenos a Borrar")
                v.geometry('800x300')

                sc = Scrollbar(v)
                sc.pack(side=RIGHT, fill=Y)

                lb = Listbox(v, yscrollcommand=sc.set)
                lb.pack(side=BOTTOM, fill=BOTH, expand=True)

                sc.config(command=lb.yview)

                for r in results:
                    lb.insert(END, r['titulo'])
                    lb.insert(END, '')

                respuesta = messagebox.askyesno(
                    title="Confirmar",
                    message="¿Está seguro que quiere eliminar estos estrenos?"
                )

                if respuesta:
                    writer = ix.writer()
                    writer.delete_by_query(query)
                    writer.commit()

                    messagebox.showinfo("Aviso", "Estrenos eliminados correctamente.")

            else:
                messagebox.showinfo(
                    "AVISO",
                    "No hay ningún estreno en ese rango de fechas."
                )

    v = Toplevel()
    v.title("Eliminar Estrenos por Fecha")

    l = Label(v, text="Introduzca fechas (DD-MM-AAAA-DD-MM-AAAA):")
    l.pack(side=LEFT)

    en = Entry(v, width=75)
    en.bind("<Return>", modificar)
    en.pack(side=LEFT)



def buscar_generos_y_titulo():
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
    
def buscar_por_sinopsis_precio_mas_barato():
    def mostrar_lista(event):
        ix=open_dir("Index")   
        with ix.searcher() as searcher:
            query = QueryParser("sinopsis", ix.schema).parse('"'+str(en.get())+'"')
            results = searcher.search(query,limit=1, sortedby="precio")
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
                            lb.insert(END,r['sinopsis'])
                            lb.insert(END,r['precio'])
                            lb.insert(END,'')

    v = Toplevel()
    v.title("Búsqueda por Título o Introducción")
        
    l1 = Label(v, text="Escriba frase de los detalles")
    l1.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    
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
            results = searcher.search(query,limit=3) #sólo devuelve los 3 primeros
            #recorremos los resultados obtenidos(es una lista de diccionarios) y mostramos lo solicitado
            v = Toplevel()
            v.title("Listado de juegos")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            #Importante: el diccionario solo contiene los campos que han sido almacenados(stored=True) en el Schema
            for r in results: 
                lb.insert(END,r['titulo'])
                lb.insert(END,r['sinopsis'])
                lb.insert(END,'')
    
    v = Toplevel()
    v.title("Busqueda por Título o Sinopsis")
    l = Label(v, text="Introduzca las palabras a buscar:")
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
    buscarmenu.add_command(label="Editorial", command=buscar_editorial)
    buscarmenu.add_command(label="Rango de precios", command=buscar_precio)
    buscarmenu.add_command(label="Género y Título", command=buscar_generos_y_titulo)
    buscarmenu.add_command(label="Eliminar por fecha", command=eliminar_por_fecha)
    buscarmenu.add_command(label="Sinopsis y Precio más bajo", command=buscar_por_sinopsis_precio_mas_barato)
    # buscarmenu.add_command(label="Título o Sinopsis", command=modificar_fecha)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

    

if __name__ == "__main__":
    ventana_principal()