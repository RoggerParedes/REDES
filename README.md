# TP N°1: File Transfer

## Ejecución de la Aplicación

Para los siguientes comandos de ejecución, se debe estar parado en la carpeta
raíz del proyecto luego de clonarlo.

### Servidor

La línea de ejecución para el **servidor** según lo indicado por la cátedra, es:

```sh
$ python3 src/start-server.py -v -H 10.0.0.1 -p 5005 -s src/data_server
```
Ademas, proporcionamos scripts para facilitar la ejecucion del servidor y los dos tipos de clientes.

Primero otorgar permisos de ejecucion con
```sh
$ chmod +x ./run_*
```

```sh
$ ./run_server
```

### Cliente

Para conectar un **cliente** que realice la operación **upload**, ejecutamos en
otra terminal:

```sh
$ python3 src/upload.py -v -H 10.0.0.1 -p 5005 -s ruta_archivo -n nombre_archivo
```
- ``ruta_archivo`` es la ruta al archivo a subir.
- ``nombre_archivo`` es el nombre que el archivo tendrá en el servidor.

O, mediante el script
```sh
$ ./run_upload /data_server pdf1
```

Para conectar un **cliente** que realice la operación **download**, ejecutamos
en otra terminal:

```sh
$ python3 src/download.py -v -H 10.0.0.1 -p 5005 -s ruta_destino -n nombre_archivo
```

- ``ruta_destino`` es la ruta en el servidor al archivo a descargar.
- ``nombre_archivo`` es el nombre que el archivo tiene en el servidor.

O, mediante el script
```sh
$ ./run_download /data_server pdf1
```

Para obtener más información de los parametros que reciben estos dos scripts
usar los siguientes comandos:

```sh
$ python3 src/upload.py --help
$ python3 src/download.py --help
```

### Ejecución de mininet (topología)

Para ejecutar mininet se utiliza el siguiente comando:

```sh
$ sudo mn --custom $PWD/topology.py --topo mytopo,2,10 --mac -x
```

- ``mytopo,2,30`` en este caso 2 es la cantidad de hosts y 10 es el % de pérdida
  de paquetes. Podemos cambiar estos valores.

Tambien podemos reemplazar toda la linea por

```sh
$ ./mininet.sh 1 10
```
Y se ejecutara la topologia desarrollada con 1 host y 10% de packet loss (segun indican los parametros a modo de ejemplo).