import ipaddress
import subprocess
import getopt
import sys
import requests
import uuid
import socket
import re
import time

# Función para obtener los datos de fabricación de una tarjeta de red por IP
def obtener_datos_por_ip(ip):
    red = "192.168.1.0/24"

    host = socket.gethostname()
    mi_ip = socket.gethostbyname(host)

    if (ip == mi_ip):
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        mac = ":".join([mac[e:e+2] for e in range(0, 11, 2)])

    elif ipaddress.ip_address(ip) in ipaddress.ip_network(red):
        try:
            tabla = subprocess.check_output(["arp", "-a"], shell=True).decode("latin-1")
            lineas = tabla.split("\n")[3:]

            encontrado = False
            for linea in lineas:
                datos = re.split(r"\s+", linea.strip())

                if datos[0] == ip:
                    mac = datos[1]
                    encontrado = True
            if not encontrado:
                print("Error: ip is outside the host network")
                return 

        except subprocess.CalledProcessError:
            print("Hubo un error al obtener la dirección MAC")

    else:
        print("Error: ip is outside the host network")
        return 
    print("MAC Address:\t" + mac)
    fabricante, tiempo =  obtener_fabricante(mac)
    print("Fabricante:\t" + fabricante)
    print(f"Tiempo de respuesta: {tiempo} ms")

# Función para obtener los datos de fabricación de una tarjeta de red por MAC
def obtener_datos_por_mac(mac):
    
    try:
        print("MAC address:\t" + mac)
        fabricante, tiempo =  obtener_fabricante(mac)
        print("Fabricante:\t" + fabricante)
        print(f"Tiempo de respuesta: {tiempo} ms")

    except Exception as e:
        print("Error al obtener fabricante")

# Función para obtener la tabla ARP
def obtener_tabla_arp():
    try:
        tabla = subprocess.check_output(["arp", "-a"], shell=True).decode("latin-1")
        lineas = tabla.split("\n")[3:]

        listaIpMac = []
        for linea in lineas:
            datos = re.split(r"\s+", linea.strip())
            if len(datos[0]) > 0 and datos[0][0].isnumeric():
                ip, mac = datos[0], datos[1]
                listaIpMac.append((ip, mac))
        
        print("IP/MAC/Vendor")
        for dato in listaIpMac:
            fabricante, tiempo = obtener_fabricante(dato[1])
            if fabricante != "Not found":
                print(f"{dato[0]}\t /   {dato[1]}   /   {fabricante}\t {tiempo}ms")

    except subprocess.CalledProcessError as e:
        print(str(e))

def obtener_fabricante(mac):
    url = f"https://api.maclookup.app/v2/macs/{mac}"

    try:
        inicioTiempo = time.time()
        response = requests.get(url)
        terminoTiempo = time.time()

        if response.status_code == 200:
            fabricante = response.text[1:-1]
            fabricante = fabricante.split(",")

            return fabricante[3][11:-1], int((terminoTiempo - inicioTiempo) * 1000)
        else:
            return "Not found"

    except Exception as e:
        return e

def main(argv):
    try:
        opts = getopt.getopt(argv, "i:m:a", ["ip=", "mac=", "arp"])[0]

    except getopt.GetoptError:
        print("""Use: python OUILookup.py --ip <IP> | --mac <IP> | --arp | [--help]
    --ip : IP del host a consultar.
    --mac: MAC a consultar. P.e. aa:bb:cc:00:00:00.
    --arp: muestra los fabricantes de los host disponibles en la tabla arp.
    --help: muestra este mensaje y termina.""")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-i", "--ip"):
            obtener_datos_por_ip(arg)
        elif opt in ("-m", "--mac"):
            obtener_datos_por_mac(arg)
        else:
            obtener_tabla_arp()

if __name__ == "__main__":
    main(sys.argv[1:])