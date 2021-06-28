import json

import websocket

ws = websocket.create_connection('ws://localhost:8545')

o = {
    "jsonrpc": "2.0",
    "method": "eth_subscribe",
    "params": [
        "newHeads",
        ],
    "id": 0,
        }

ws.send(json.dumps(o).encode('utf-8'))

while True:
    print(ws.recv())

ws.close()
