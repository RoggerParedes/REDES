#! /bin/bash

# $1 -> ruta local del archivo a cargar en el servidor
# $2 -> nombre con el que se cargara en el servidor
if [ $# -ne 2 ]
  then
    echo "Se necesitan 2 argumentos"
fi

python3 src/upload.py -v -H 127.0.0.0 -p 12000 -s $1 -n $2
