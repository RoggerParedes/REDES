#! /bin/bash

# $1 -> cantidad de hosts
# $2 -> % de packet loss

if [ $# -ne 2 ]
  then
    echo "Se necesitan 2 argumentos"
fi

sudo mn --custom $PWD/src/lib/topology.py --topo mytopo,$1,$2 --mac -x # el -x abre xterm
