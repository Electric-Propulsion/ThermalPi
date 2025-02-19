"""
Node which reads from the TC-08 Datalogger and acts as a server which can send data back to the main Pi.
"""

import websockets
import asyncio
import json

from picousbtc08 import PicoUSBTC08

async def handler(sock: websockets.websocket):
    try:
        pico = PicoUSBTC08()

        while True:
            # Data format: {'command': <command>, 'param1': <param1>, 'param2': <param2>, ...}
            # Where param1, param2, ... are customized to the command
            received = await sock.recv()
            command = json.loads(received)

            if command["command"] == "open_instrument":
                pico.open_instrument()

            elif command["command"] == "enable_sampling":
                pico.enable_sampling(command["sampling_interval"])

            elif command["command"] == "disable_sampling":
                pico.disable_sampling()

            elif command["command"] == "configure_channel":
                pico.configure_channel(command["channel"], command["type"])

            elif command["command"] == "disable_channel":
                pico.disable_channel(command["channel"])

            elif command["command"] == "measure_all_channels":
                pico.measure_all_channels()
                keys = [f"ch_{i}" for i in range(len(pico.channel_data))]
                vals = [pico.channel_data[i].last_measurement for i in range(len(pico.channel_data))]
                data = {k:v for (k,v) in zip(keys, vals)}
                await sock.send(json.dumps(data))
    
    except websockets.ConnectionClosedError:
        print("Connection closed.")
    finally:
        pico.close_instrument()
        

async def main():
    async with websockets.serve(handler, "", 8001) as server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())