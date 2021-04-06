#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal, select, socket, json, sys, os, re                                #Funciones orientadas a conexión, sistema, json y expresiones regulares
from time import time                                                           #Cronometrar tiempos
from time import sleep

RED = "\033[93m"
END = "\033[0m"
BAR = "\n———————————————————————————————————————\n"

expIPv4 = "((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"  #Expresión regular dir IP
expPort = "(6553[0-5]|655[0-2][0-9]|65[0-4][0-9]{2}|6[0-4][0-9]{3}|[0-5]?([0-9]){0,3}[0-9])"     #Expresión regular puerto

if __name__ == "__main__":
    if len(sys.argv) != 2 :
        print(RED + "ERR: Nº de argumentos no válidos" + END)
        sys.exit()

    #Variables socket
    servIP = "127.0.0.1"
    servPort = int(sys.argv[1])
    serv_addr = (servIP, servPort)

    if servPort < 1023:                                                         #Comprobamos el nº de puerto
        print(RED + "ERR: El nº de puerto debe ser mayor que 1023" + END)
        sys.exit()

    #Creación del socket servidor de direcciones peers
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)                                                         #Establecemos modo no bloqueo

    #Conexión socket
    sock.bind(serv_addr)

    sock.listen(10)                                                             #El socket está a la escucha de clientes
    inputs = [sock]                                                             #Lista de sockets de entrada
    outputs = []                                                                #Lista de sockets de salida

    cliServ = {}
    cliServ["clientes"] = []

    while True:
        try:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)     #Select coordina entre i/o

            for sck in readable:                                                #Sockets de entrada disponibles
                if sck == sock:                                                 #Un nuevo socket desea conectarse
                    cli, cli_add = sock.accept()                                #Aceptamos la conexión de un socket "readable"
                    cli.setblocking(0)                                          #Establecemos modo no bloqueo
                    print("-Cliente:", cli_add, "conectado")

                    inputs.append(cli)                                          #Añadimos a la lista inputs
                    outputs.append(cli)                                         #Añadimos a la lista outputs

                    data = str(json.dumps(cliServ))                             #Convertimos JSON en string
                    cli.send(data.encode())                                     #Enviamos lista codificada a el nuevo cliente

                else:
                    cliServ_addr = sck.getpeername()
                    dataRecv = sck.recv(1024)

                    if dataRecv:
                        dataRecv = str(dataRecv.strip().decode('utf-8'))        #Decodificamos la información recibida
                        
                        addValido = re.compile(r"^\('"+ expIPv4 + "'," + expPort + "\)$")   #Comprobamos que es una tupla ('IP', port)

                        if addValido != None:
                            #Almacenamos la direccion de escucha del peer junto con el socket de conexión de este servidor
                            cliServ["clientes"].append({"peerServ_addr" : str(dataRecv), "cliServ_addr": str(cliServ_addr)})
                            print(BAR[:-30] + "JSON actualizado" + BAR[1:-29])
                            print(RED ,cliServ, END)
                            print(BAR)

                        else:
                            print(dataRecv)

                    else:
                        inputs.remove(sck)                                      #Eliminamos el socket de la lista de inputs
                        outputs.remove(sck)                                     #Eliminamos el socket de la lista de outputs
                        sck.close()

                        n = 0
                        for p in cliServ["clientes"]:                           #Eliminamos del JSON
                            if p["cliServ_addr"] == str(cliServ_addr):
                                cliServ["clientes"].pop(n)
                            n += 1

                        print("-Cliente:", cliServ_addr, "desconectado")
                        print(BAR[:-29] + "JSON actualizado" + BAR[1:-28])
                        print(RED , cliServ, END)
                        print(BAR)


            for sck in exceptional:                                             #Condiciones excepcionales
                inputs.remove(sck)                                              #Eliminamos el socket de la lista de inputs
                outputs.remove(sck)                                             #Eliminamos el socket de la lista de outputs
                sck.close()                                                     #Cerramos el socket
        
        except KeyboardInterrupt:
            print("\nCerrando conexión con clientes")
            sys.exit()