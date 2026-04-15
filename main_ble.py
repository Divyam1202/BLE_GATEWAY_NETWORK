from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import (
    CharacteristicReadOptions,
    CharacteristicWriteOptions,
    CharacteristicFlags as CharFlags,
    characteristic,
)
import subprocess
import struct
import asyncio

from bluez_peripheral.util import Adapter, get_message_bus
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.agent import NoIoAgent


class BLE(Service):
    BLE_write = characteristic("BEF1", CharFlags.WRITE)

    def __init__(self, mac_Address):
        # Base 16 service UUID, This should be a primary service.
        super().__init__("BEEF", True)
        self.mac_address = mac_Address
        self.DC_ble = b"\x00\x00"

    @BLE_write.setter
    def any_write(
        self, value: bytes, options: CharacteristicWriteOptions
    ) -> None:
        print(f"{value.decode()}")
        #--------------------------------------------------------------

        result = subprocess.run([value], stdout=subprocess.PIPE, text=True)
        print(result.stdout)

    @characteristic("BEF2", CharFlags.READ | CharFlags.NOTIFY)
    def display_BLE(self, options: CharacteristicReadOptions) -> bytes:
        return self.DC_ble

    def my_writeonly_characteristic(
        self, value: bytes, options: CharacteristicWriteOptions
    ) -> None:
        # Your characteristics will need to handle bytes.
        self._some_value = value

    #--------------------------------------------------------------------------
    def write_BLE(self, new_rate: int) -> None:
        flags = 0
        rate = struct.pack("<BB", flags, new_rate)
        self.DC_ble = rate
        self.display_BLE.changed(rate)

async def main():
    # Alternativly you can request this bus directly from dbus_next.
    bus = await get_message_bus()

    service = BLE("AA:BB:CC:DD:EE:FF")
    await service.register(bus)

    # An agent is required to handle pairing 
    agent = NoIoAgent()
    # This script needs superuser for this to work.
    await agent.register(bus)

    adapter = await Adapter.get_first(bus)

    # Start an advert that will last for 60 seconds.
    advert = Advertisement("Viit_BLE", ["180D"], 0x0340, 60)
    await advert.register(bus, adapter)

    while True:
       
        # Handle dbus requests.
        # Add a print statement to display a message.
        #print("Heart rate updated to 80")
        
        print("Write your Command:\n")
        try:
            
            print("")

        except ValueError:
            print("Invalid input. Please enter a valid integer.")
            continue
        await asyncio.sleep(10)

    await bus.wait_for_disconnect()

if __name__ == "__main__":
    asyncio.run(main())
