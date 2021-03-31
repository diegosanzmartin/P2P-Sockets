#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal, queue, select, socket, json, sys, os                             #Funciones orientadas a conexión, sistema
from time import time                                                           #Cronometrar tiempos
from time import sleep

ERR = "\033[93m"
END = "\033[0m"
BAR = "\n———————————————————————————————\n"

if __name__ == "__main__":
    if len(sys.argv) != 3 :                                                     #Esta función compara los tiempos para
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
    while len(name) <= 0:
        name = input("Nombre: ")

    #Creación del socket TCP servidor
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.connect(serv_addr)

    #Creación del socket TCP escucha servPeer
    servPeer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servPeer.setblocking(0) 
    servPeer.bind(("",0))
    servPeer.listen(10)

    servPeer_addr = servPeer.getsockname()

    data = serv.recv(1024)
    peers = json.loads(data.decode("utf-8"))
    serv.send(str(servPeer_addr).encode())

    #Conexión con peers

    inputs = [sys.stdin, servPeer]
    que = queue.Queue()

    mssNext = str.encode("")

    sckPeers = []

    for peer in peers["clientes"]:
        print("Conectando con peer:", peer["peerServ_addr"])
        cliPeer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliPeer.connect(eval(peer["peerServ_addr"]))
        inputs.append(cliPeer)
        sckPeers.append(cliPeer)

    while True:
        try:
            readable, writable, exceptional = select.select(inputs, [], [])

            for sck in readable:
                if sck == sys.stdin:
                    mssIn = sys.stdin.readline()
                    mss = "->" + name + ": " + mssIn
                    que.put(mss.encode())
                    for s in sckPeers:
                        s.send(mss.encode())

                elif sck == servPeer:                                         
                    cli, cli_add = servPeer.accept()                                #Aceptamos la conexión de un socket "readable"
                    cli.setblocking(0)                                              #Establecemos modo no bloqueo
                    print("-Cliente:", cli_add, "conectado")

                    inputs.append(cli)                                              #Añadimos a la lista inputs
                    sckPeers.append(cli)

                    peers["clientes"].append({"cliServ_addr": str(cli_add)})


                else:
                    dataRecv = sck.recv(1024)
                    if dataRecv:
                        dataRecv = dataRecv.strip().decode('utf-8')
                        print(dataRecv)

                    else:
                        sckPeers.remove(sck)
                        inputs.remove(sck)

                        cliClose = sck.getsockname()
                        sck.close()

                        n = 0
                        for p in peers["clientes"]:
                            if p["cliServ_addr"] == str(cliClose):
                                peers["clientes"].pop(n)
                            n += 1
                        print("-Cliente:", cliClose, "desconectado")

            for sck in exceptional:
                if sck == servPeer:
                    servPeer.close()

        except KeyboardInterrupt:
            servPeer.close()
            sys.exit()