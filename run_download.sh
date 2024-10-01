#! /bin/bash

# $1 -> ruta del servidor donde se almacena el archivo que quiero descargar
# $2 -> nombre del archivo que deseo descargar desde el servidor

if [ $# -ne 2 ]
  then
    echo "Se necesitan 2 argumentos"
fi

python3 src/download.py -v -H 10.0.0.1 -p 5005 -d $1 -n $2
