import asyncio
import argparse
from bleak import BleakScanner, BleakClient
from escpos.printer import Bluetooth


async def scan(args):
    """Scan for Bluetooth devices and print their basic details. Will search
    the devices' names and IDs if the 'device' argument is provided.
    """
    devices = await BleakScanner.discover()
    for d in devices:
        not (q := args.device) or (q in d.name or q in d.address) and print(d)


async def list_characteristics(args, find=None):
    """List all characteristics of a device and their properties, or call with
    find (e.g. find='write') to return the handle of the first characteristic
    with the given property (used to guess which to send to).
    """
    async with BleakClient(args.device) as client:
        services = await client.get_services()
        for _, c in services.characteristics.items():
            if find and (find in c.properties):
                return c.handle
            print(c, c.properties)
        return None


async def test_print(args):
    """Print some text and a QR code showing the capabilities of ESCPOS"""
    if not args.characteristic:
        # Try to guess the characteristic to write to if one isn't supplied
        args.characteristic = await list_characteristics(args, find="write")
        if not args.characteristic:
            return

    # The next two lines instantiate the devive by address and then create an
    # Escpos object from it. Everything apart from these 9 lines is about
    # finding the device address, and messing with Bluetooth
    async with BleakClient(args.device) as client:
        p = Bluetooth(client, args.characteristic)
        p.set(align="center", double_height=True, double_width=True)
        p.textln("E S C   P O S")
        p.qr("https://github.com/python-escpos", size=6, center=True)
        p.set(align="center")
        p.textln("Testing Bluetooth printer")
        p.ln(2)
        await p.close()


async def main(args):
    """Entry point, run one of the functions depending on the args."""
    if args.scan:
        await scan(args)
    elif args.device and args.list:
        await list_characteristics(args)
    elif args.device:
        await test_print(args)


parser = argparse.ArgumentParser(
    description="Interact with a Bluetooth ESC/POS printer"
)
parser.add_argument(
    "device",
    action="store",
    nargs="?",
    default=None,
    help="Device address (ID on MacOS) to print to, list characteristics, or search for",
)
parser.add_argument(
    "characteristic",
    type=int,
    action="store",
    nargs="?",
    default=None,
    help="Characteristic to send data to, will use first writeable characteristic if omitted",
)
parser.add_argument(
    "--scan",
    "-s",
    action="store_true",
    default=False,
    help="Scan for Bluetooth devices and return their names and IDs/addresses",
)
parser.add_argument(
    "--list",
    "-l",
    action="store_true",
    default=False,
    help="List characteristics of the given device and their properties",
)

args = parser.parse_args()
if not (args.device or args.scan):
    parser.print_help()
else:
    asyncio.run(main(args))
