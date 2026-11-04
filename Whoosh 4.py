
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
from datetime import datetime
from whoosh import qparser, index, query

# Líneas para evitar error SSL
import ssl

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def cargar():
    respuesta = messagebox.askyesno(
        title="Confirmar",
        message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta"
    )
    if respuesta:
        almacenar_datos()


def extraer_pelis():

    indices = [1, 2, 3]
    datos = []

    for i in indices:

        url = f"https://www.elseptimoarte.net/estrenos/2024/{i}/"

        try:
            f = urllib.request.urlopen(url)
            s = BeautifulSoup(f, "lxml")

            lista = s.find("ul", class_="elements")

            if lista is None:
                continue

            enlaces = lista.find_all("li")

            for elemento in enlaces:

                if not elemento.h3 or not elemento.h3.a:
                    continue

                peli = elemento.h3.a['href']

                url_peli = f"https://www.elseptimoarte.net{peli}"

                f2 = urllib.request.urlopen(url_peli)
                s2 = BeautifulSoup(f2, "lxml")

                informativo = s2.find(
                    "main",
                    class_="informativo"
                )

                if informativo is None:
                    continue

                highlight = informativo.find(
                    "section",
                    class_="highlight"
                )

                if highlight is None:
                    continue

                datos_peli = highlight.find("dl")

                if datos_peli is None:
                    continue

                # Título original
                dt_titulo_original = datos_peli.find(
                    "dt",
                    string="Título original"
                )

                if dt_titulo_original:
                    dd = dt_titulo_original.find_next_sibling("dd")

                    if dd:
                        titulo_original = dd.get_text(strip=True)
                    else:
                        titulo_original = ""
                else:
                    titulo_original = ""

                # Sinopsis
                info = s2.find("div", class_="info")

                sinopsis = info.find_all("p") if info else []

                texto = ""

                for parrafo in sinopsis:
                    texto = texto + parrafo.get_text() + "\n"

                # Título
                dt_titulo = datos_peli.find(
                    "dt",
                    string="Título"
                )

                if dt_titulo:
                    dd = dt_titulo.find_next_sibling("dd")

                    if dd:
                        titulo = dd.get_text(strip=True)
                    else:
                        titulo = titulo_original
                else:
                    titulo = titulo_original

                # País
                dt_pais = datos_peli.find(
                    "dt",
                    string="País"
                )

                if dt_pais:
                    dd = dt_pais.find_next_sibling("dd")

                    if dd:
                        pais = "".join(dd.stripped_strings)
                    else:
                        pais = ""
                else:
                    pais = ""

                # Fecha
                dt_fecha = datos_peli.find(
                    "dt",
                    string="Estreno en España"
                )

                fecha = None

                if dt_fecha:
                    dd = dt_fecha.find_next_sibling("dd")

                    if dd:
                        texto_fecha = dd.get_text(strip=True)

                        try:
                            fecha = datetime.strptime(
                                texto_fecha,
                                '%d/%m/%Y'
                            )
                        except ValueError:
                            fecha = None

                # Géneros y director
                generos_director = s2.find(
                    "div",
                    id="datos_pelicula"
                )

                generos = ""
                director = ""

                if generos_director:

                    p_generos = generos_director.find(
                        "p",
                        class_="categorias"
                    )

                    if p_generos:
                        generos = "".join(
                            p_generos.stripped_strings
                        )

                    p_director = generos_director.find(
                        "p",
                        class_="director"
                    )

                    if p_director:
                        director = "".join(
                            p_director.stripped_strings
                        )

                # Guardar los datos de la película
                datos.append((
                    titulo,
                    titulo_original,
                    fecha,
                    pais,
                    generos,
                    director,
                    texto,
                    url_peli
                ))

                print(datos[-1])

        except Exception as e:
            print(f"Error al procesar {url}: {e}")

    return datos

def almacenar_datos():
    #define el esquema de la información
    schem = Schema(titulo=ID(stored=True), titulo_original=TEXT(stored=True), fecha=DATETIME(stored=True), pais=TEXT(stored=True), director=TEXT(stored=True), generos=KEYWORD(stored=True,commas=True) ,texto=TEXT(stored=True), url_peli=TEXT(stored=True))
    
    #eliminamos el directorio del índice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    
    #creamos el índice
    ix = create_in("Index", schema=schem)
    #creamos un writer para poder añadir documentos al indice
    writer = ix.writer()
    i=0
    lista=extraer_pelis()
    for j in lista:
        #añade cada juego de la lista al índice
        writer.add_document(titulo=str(j[0]), titulo_original=str(j[1]), fecha=j[2], pais=str(j[3]), director=str(j[4]), generos=str(j[5]), texto=str(j[6]), url_peli=str(j[7]))    
        i+=1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " pelis")

def imprimir_lista(cursor):
    v = Toplevel()
    v.title("RECETAS DE COCINA DE RECETAS GRATIS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row['titulo'])
        lb.insert(END,row['titulo_original'])
        lb.insert(END,"    Fecha: "+ datetime.strftime(row['fecha'],"%d/%m/%Y"))
        lb.insert(END,row['pais'])
        lb.insert(END,row['generos'])
        lb.insert(END,row['director'])
        lb.insert(END,row['texto'])
        lb.insert(END,row['url_peli'])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)
    
def buscar_generos():
    def mostrar_lista(event):
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            if(len(str(en.get()).split(" ")) == 1) :
                entrada = '"'+str(en.get().strip())+'"'
                query = QueryParser("generos", ix.schema).parse(entrada)
                results = searcher.search(query,limit=20)
                imprimir_lista(results)
            else:
                messagebox.showerror(title="Error",message="¿Qué es Vinland?")   
    v = Toplevel()
    v.title("Búsqueda por Título o Introducción")
        
    l1 = Label(v, text="Escriba frase del título o introducción:")
    l1.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    
def buscar_titulo_o_sinopsis():
    def mostrar_lista(event):
        ix=open_dir("Index")   
        with ix.searcher() as searcher:
            query = MultifieldParser(["titulos", "textos"], ix.schema).parse('"'+ str(en.get()) + '"')
            results = searcher.search(query,limit=10)
            imprimir_lista(results)

    v = Toplevel()
    v.title("Búsqueda por Título o Introducción")
        
    l1 = Label(v, text="Escriba frase del título o introducción:")
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
    buscarmenu.add_command(label="Título o Sinopsis", command=buscar_titulo_o_sinopsis)
    buscarmenu.add_command(label="Géneros", command=buscar_generos)
    # buscarmenu.add_command(label="Fecha", command=buscar_fecha)
    # buscarmenu.add_command(label="Modificar fecha", command=modificar_fecha)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

    

if __name__ == "__main__":
    ventana_principal()