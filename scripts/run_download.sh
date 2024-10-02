#! /bin/bash

# $1 -> ruta donde quiero almacenar el archivo que voy a descargar
# $2 -> nombre del archivo en el servidor

if [ $# -ne 2 ]
  then
    echo "Se necesitan 2 argumentos"
fi

cd ..
python3 src/download.py -v -H 127.0.0.0 -p 12000 -d $1 -n $2