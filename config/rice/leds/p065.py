"""DayBetter P065 LED strips over Bluetooth LE (their protocol, reverse-engineered by ma67-ex/ClaudeLamp and
jnstockley/daybetter-ble-client): frames A0 <cmd> <len> <payload> <crc16-modbus, little-endian>."""
import asyncio

from bleak import BleakClient

WRITE = "0000a065-0000-1000-8000-00805f9b34fb"
NOTIFY = "0000f065-0000-1000-8000-00805f9b34fb"


def crc(data):
    c = 0xFFFF
    for b in data:
        c ^= b
        for _ in range(8):
            c = (c >> 1) ^ 0xA001 if c & 1 else c >> 1
    return c.to_bytes(2, "little")


def frame(cmd, *payload):
    body = bytes([0xA0, cmd, len(payload) + 3, *payload])
    return body + crc(body)


assert frame(0x11, 1).hex() == "a0110401b121" and frame(0x15, 255, 0, 0).hex() == "a01506ff000025c0"


class Strip:
    def __init__(self, addr, log=print):
        self.addr, self.log = addr, log
        self.client = None
        self.replies = asyncio.Queue()

    def _notify(self, _, data):
        self.replies.put_nowait(bytes(data))

    async def _send(self, f, want=None, wait=2.0):
        while not self.replies.empty():
            self.replies.get_nowait()
        await self.client.write_gatt_char(WRITE, f, response=True)
        if want is None:
            return None
        try:
            while True:
                r = await asyncio.wait_for(self.replies.get(), wait)
                if len(r) > 1 and r[0] == 0xA1 and r[1] == want:
                    return r
        except asyncio.TimeoutError:
            return None

    async def connect(self):
        self.client = BleakClient(self.addr, timeout=20, disconnected_callback=lambda _: self.log("disconnected"))
        await self.client.connect()
        await self.client.start_notify(NOTIFY, self._notify)
        # some firmware wants a handshake (CCHIP, then echo its challenge back); harmless where it doesn't
        r = await self._send(frame(0x00, *b"CCHIP"), want=0x00)
        if r and r[3:8] == b"CCHIP":
            ok = await self._send(frame(0x01, *r[3:10]), want=0x01)
            self.log("handshake", "ok" if ok else "no answer")

    @property
    def connected(self):
        return bool(self.client and self.client.is_connected)

    async def close(self):
        if self.client:
            await self.client.disconnect()

    async def power(self, on):
        return await self._send(frame(0x11, 1 if on else 0), want=0x11)

    async def brightness(self, pct):
        return await self._send(frame(0x13, max(1, min(100, round(pct)))), want=0x13)

    async def colour(self, r, g, b, ack=True):
        return await self._send(frame(0x15, r, g, b, 0xFF), want=0x15 if ack else None)
