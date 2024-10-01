#! /bin/bash

if [ $# -ne 2 ]
  then
    echo "Se necesitan 2 argumentos"
fi

sudo mn --custom $PWD/topology.py --topo mytopo,$1,$2 --test pingall