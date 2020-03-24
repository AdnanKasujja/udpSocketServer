import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0


clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      #if address from socket exists is already in clientlist
      #therefore client already connected
      if addr in clients:
         data = data[2:-1]
         print(data)
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
         else:
            playerInfo = json.loads(data)
            print("")
            print(playerInfo)
            print("")
            clients[addr]['position'] = playerInfo['position']
            clients[addr]['rotation'] = playerInfo['rotation']
      else:
         if 'connect' in data:
            #if the request from the client connects
            print(" ")
            print("New client connected")
            print(" ")
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
            clients[addr]['position'] = 0
            clients[addr]['rotation'] = 0
            message = {"cmd": 0,"player":{"id":str(addr)}}
            message["player"]["color"] = clients[addr]["color"]
            connectedClients = {"cmd": 3, "players": []}
            m = json.dumps(message)
            for c in clients:
               if c != addr:
                  sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
                  player = {}
                  player['id'] = str(c)
                  player['color'] = clients[c]['color']
                  player['position'] = clients[c]['position']
                  player['rotation'] = clients[c]['rotation']
                  connectedClients['players'].append(player)
            message["cmd"] = 4
            m = json.dumps(message)
            sock.sendto(bytes(m,'utf8'), (addr[0],addr[1]))
            m = json.dumps(connectedClients)
            sock.sendto(bytes(m,'utf8'), (addr[0],addr[1]))

def cleanClients(sock):
   while True:
      message = {"cmd": 2,"players":[]}
      anyDropped = False
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            anyDropped = True
            print('Dropped Client: ', c)
            message['players'].append({"id":str(c)})
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
      if anyDropped:
         m = json.dumps(message)
         for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         player['id'] = str(c)
         player['position'] = clients[c]['position']
         player['rotation'] = clients[c]['rotation']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(0.033)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
