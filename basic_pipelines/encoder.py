from typing import Tuple, List
from mcp2515 import MCP2515
from datetime import datetime, timedelta
from time import monotonic

class CANEncoder:

    def __init__(self) -> None:
        self.mcp2515: MCP2515 | None = None
        self.start_time = datetime.now()
        self.last_heartbeat = monotonic()

    def callMCP2515Instance(self) -> "CANEncoder":
        if self.mcp2515 is None:
            # print("@@@@@@@@@@@@@@@@@@")
            self.mcp2515 = MCP2515()
            self.mcp2515.initMcp2515()
        return self

    def sendSteering(self, steering_channels: Tuple[int, ...]):
        
        if self.mcp2515 is None:
            print("MCP2515 instantie niet geïnitialiseerd")
            return

        can_id: int = 0x200
        data: List[int] = []

        for value in steering_channels:
        
            # Verdeel elke 16-bit waarde van iBUS stuurkanalen in twee 8-bit bytes (big-endian).
            # In iBUS zijn kanaalwaarden 16-bit integers, bijv. 1500 (0x05DC in hex). 
            # Omdat een CAN-bus maximaal 8 bytes per bericht ondersteunt, moeten we elk kanaal 
            # opdelen in twee afzonderlijke bytes: een high byte en een low byte.
            #
            # Voorbeeld: 
            #     value = 1500 = 0x05DC = 00000101 11011100 (in binaire 16 bits)
            #
            # (value >> 8) verschuift de bits 8 posities naar rechts:
            #     00000101 11011100  →  00000000 00000101  → high byte (0x05)
            #
            # value & 0xFF haalt de onderste 8 bits eruit - & = bitwise AND:
            #     00000101 11011100  &  00000000 11111111  = 11011100  → low byte (0xDC)
            #
            # Resultaat:
            #     high = 0x05
            #     low  = 0xDC
            #
            # Deze worden toegevoegd aan een CAN-data array, zodat we de stuurinformatie 
            # byte-per-byte kunnen versturen via de CAN-bus.
            value = max(1000, min(2000, value))
            high: int = (value >> 8) & 0xFF
            low: int = value & 0xFF

            data.append(high)
            data.append(low)

        # print(f"CAN-data: {can_id:03X} [{len(data)}] {' '.join(f'{b:02X}' for b in data)}")

        self.mcp2515.sendCanMessage(can_id, data)

    def triggerFailsafe(self) -> None:
        if self.mcp2515 is None:
            return
        print("Triggering failsafe: Stopping motors")
        can_id: int = 0x100
        data = [0x05, 0xDC, 0x05, 0xDC, 0x05, 0xDC]  # (1500, 1500, 1500)
        self.mcp2515.sendCanMessage(can_id, data)
        
    def sendHeartbeat(self) -> None:
        if self.mcp2515 is None:
            print("mcp2515 is None, exiting sendHeartbeat")
            return
        now = monotonic()
        time_diff = now - self.last_heartbeat
        # print(f"sendHeartbeat: now={now:.3f}, last_heartbeat={self.last_heartbeat:.3f}, diff={time_diff:.3f}s")
        
        counter = 65 # moet 125 worden == 1 seconden
        if now >= self.last_heartbeat + 1:
            can_id: int = 0x050
            data = [0x01]
            try:
                self.last_heartbeat = now
                if counter >= 65:
                    self.mcp2515.sendCanMessage(can_id, data)
                    print(f"Verstuur heartbeat: ID=0x{can_id:03X}, Data={data}")
                counter += 1
                print(counter)
            except Exception as e:
                print(f"Fout bij versturen heartbeat: {e}")
                pass
        # else:
        #     print(f"Heartbeat niet verzonden: diff={time_diff:.3f}s < 1s")