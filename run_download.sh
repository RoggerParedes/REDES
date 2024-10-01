#! /bin/bash

# $1 -> ruta del servidor donde se almacena el archivo
# $2 -> nombre del archivo que deseo descargar desde el servidor

if [ $# -ne 2 ]
  then
    echo "Se necesitan 2 argumentos"
fi

python3 src/download.py -v -H 127.0.0.0 -p 12000 -d $1 -n $2
