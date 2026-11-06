#1.b

def imprimir_lista(cursor):
    
    v = Toplevel()
    v.title("JUEGOS DE MESA")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row['titulo'])
        lb.insert(END,"    Sinopsis: "+ str(row['sinopsis']))
        lb.insert(END,"    Fecha: "+ datetime.strftime(row['fecha'], "%d/%m/%Y"))
        lb.insert(END,"    Generos: "+ str(row['generos']))
        lb.insert(END,"    Editorial: "+ str(row['editorial']))
        lb.insert(END, "    Precio: " + str(row['precio']))
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)


def listar_todo():
            ix=open_dir("Index")
            with ix.searcher() as searcher:
                results = searcher.search(query.Every(),limit=None)
                imprimir_lista(results)