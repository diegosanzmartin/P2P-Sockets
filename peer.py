#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal, queue, select, socket, json, sys, os                             #Funciones orientadas a conexión, sistema, json y expresiones regulares
from time import time                                                           #Cronometrar tiempos
from time import sleep

ERR = "\033[93m"
END = "\033[0m"
BAR = "\n———————————————————————————————\n"

if __name__ == "__main__":
    if len(sys.argv) != 3 :                                                     
        print(ERR + "ERR: Nº de argumentos no válidos" + END)
        sys.exit()

    #Variables socket servidor
    servIP = sys.argv[1]
    servPort = int(sys.argv[2])
    serv_addr = (servIP, servPort)
    
    if servPort < 1023:                                                         #Comprobamos el nº de puerto
        print(ERR + "ERR: El nº de puerto debe ser mayor que 1023" + END)
        sys.exit()

    name = ""
    while len(name) <= 0:                                                       #Solicitamos el nombre
        name = input("Nombre: ")

    #Creación del socket TCP servidor
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.connect(serv_addr)                                                     #Establecemos conexión con el servidor

    #Creación del socket TCP escucha servPeer
    servPeer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servPeer.setblocking(0)                                                     #Establecemos modo no bloqueo
    servPeer.bind(("",0))
    servPeer.listen(10)                                                         #El socket está a la escucha

    servPeer_addr = servPeer.getsockname()                                      #Obtenemos la dirección del servidor

    data = serv.recv(1024)
    peers = json.loads(data.decode("utf-8"))                                    #Guardamos la información en un JSON
    serv.send(str(servPeer_addr).encode())

    #Conexión con peers
    inputs = [sys.stdin, servPeer]                                              #Lista de servidores de entrada
    que = queue.Queue()                                                         #Creamos una cola

    mssNext = str.encode("")

    sckPeers = []                                                               #Lista de sockets servidor de los demás usuarios

    for peer in peers["clientes"]:                                              
        print("Conectando con peer:", peer["peerServ_addr"])
        cliPeer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliPeer.connect(eval(peer["peerServ_addr"]))
        inputs.append(cliPeer)                                                  #Añadimos al final de la lista inputs
        sckPeers.append(cliPeer)                                                #Añadimos al final de la lista de sockets servidor                                                 

    while True:
        try:
            readable, writable, exceptional = select.select(inputs, [], [])     #Select coordina entre i/o

            for sck in readable:                                                #Sockets de entrada disponibles
                if sck == sys.stdin:                                            #Si detecta el teclado
                    mssIn = sys.stdin.readline()                                
                    mss = "->" + name + ": " + mssIn
                    que.put(mss.encode())                                       #Añadimos el mensaje a la cola
                    for s in sckPeers:
                        s.send(mss.encode())

                elif sck == servPeer:                                           #Un nuevo servidor "peer" desea conectarse                                       
                    cli, cli_add = servPeer.accept()                            #Aceptamos la conexión de un socket "readable"
                    cli.setblocking(0)                                          #Establecemos modo no bloqueo
                    print("-Cliente:", cli_add, "conectado")

                    inputs.append(cli)                                          #Añadimos al final de la lista inputs
                    sckPeers.append(cli)                                        #Añadimos al final de la lista de sockets servidor

                    peers["clientes"].append({"cliServ_addr": str(cli_add)})


                else:
                    dataRecv = sck.recv(1024)
                    if dataRecv:
                        dataRecv = dataRecv.strip().decode('utf-8')
                        print(dataRecv)

                    else:
                        sckPeers.remove(sck)                                    #Eliminamos el socket de la lista de sckPeers
                        inputs.remove(sck)                                      #Eliminamos el socket de la lista de inputs

                        cliClose = sck.getsockname()
                        sck.close()                                             #Cerramos el socket

                        n = 0
                        for p in peers["clientes"]:                             #Eliminamos del JSON
                            if p["cliServ_addr"] == str(cliClose):
                                peers["clientes"].pop(n)
                            n += 1
                        print("-Cliente:", cliClose, "desconectado")

            for sck in exceptional:                                             #Condiciones excepcionales
                if sck == servPeer:
                    servPeer.close()

        except KeyboardInterrupt:
            servPeer.close()
            sys.exit()