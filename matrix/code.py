import time
import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal, Graphics
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
import adafruit_connection_manager
import adafruit_requests
from adafruit_esp32spi import adafruit_esp32spi
import os
from digitalio import DigitalInOut
import busio
import displayio
import gc
from secrets import DATA_SOURCE,NE_CORNER,SW_CORNER


## CONSTANTS

FLIGHT_CHANGE = 5
MAX_FLIGHTS = 8
MAX_TEXT_LEN = 8


## LOADING FROM FILES
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
big_font = bitmap_font.load_font("/fonts/6x9.bdf")



def get_loc(lat,long, num_pix_x=32,num_pix_y=32):
    pix_y = int((NE_CORNER[0] - lat) / (NE_CORNER[0] - SW_CORNER[0]) * num_pix_y) - 1
    pix_x = num_pix_x - int((NE_CORNER[1] - long) / (NE_CORNER[1] - SW_CORNER[1]) * num_pix_x)
    return (pix_x,pix_y)

def dest_label(dest,x=40,y=12,color=0x00FF00):
    lab = label.Label(font=big_font,text=dest,color=color)
    lab.x = x
    lab.y = y
    return lab

def orig_label(orig,x=40,y=5,color=0x00FF00):
    lab = label.Label(font=big_font,text=orig,color=color)
    lab.x = x
    lab.y = y
    return lab

def flight_label(flight,x=34,y=26,color=0x0000FF):
    lab = label.Label(font=big_font,text=flight,color=color)
    lab.x = x
    lab.y = y
    return lab



esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

if "SCK1" in dir(board):
    spi = busio.SPI(board.SCK1, board.MOSI1, board.MISO1)
else:
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

pool = adafruit_connection_manager.get_radio_socketpool(esp)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp)
requests = adafruit_requests.Session(pool, ssl_context)


print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(ssid, password)
    except OSError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", esp.ap_info.ssid, "\tRSSI:", esp.ap_info.rssi)
print("My IP address is", esp.ipv4_address)

matrixportal = MatrixPortal(esp=esp)

display = matrixportal.graphics.display


superroot = displayio.Group()
display.root_group = superroot
last_call = time.monotonic()
flightdots = displayio.Bitmap(64,32,4)


palette = displayio.Palette(4)
palette[0] = 0x000000 # OFF
palette[1] = 0xFFFFFF # WHITE
palette[2] = 0xa102d6 # PURPLE (highlighted/active flight)
palette[3] = 0x00FF00 # GREEN (receiver location marker)
tile_grid = displayio.TileGrid(flightdots, pixel_shader=palette)
superroot.append(tile_grid)

# Permanent 2x2 marker for the receiver's own location, hardcoded at the
# center of the 32x32 grid. Never cleared by the per-cycle dot-clearing
# logic below.
receiver_pixels = {(15, 15), (16, 15), (15, 16), (16, 16)}
for px, py in receiver_pixels:
    flightdots[px, py] = 3

# Fixed pool of MAX_FLIGHTS display slots, built once at boot. Updating a
# slot's label .text / dot position in place (instead of building new
# displayio.Group/Label objects every cycle) avoids the heap fragmentation
# that repeated allocation of displayio objects causes on CircuitPython.
root = displayio.Group()
slot_groups = []
orig_labels = []
dest_labels = []
flight_labels = []
slot_x = [0] * MAX_FLIGHTS
slot_y = [0] * MAX_FLIGHTS
num_active = 0
current = 0

for _ in range(MAX_FLIGHTS):
    o_lab = orig_label(" " * 4)
    d_lab = dest_label(" " * 4)
    f_lab = flight_label(" " * MAX_TEXT_LEN)

    slot_group = displayio.Group()
    slot_group.append(o_lab)
    slot_group.append(d_lab)
    slot_group.append(f_lab)
    slot_group.hidden = True

    root.append(slot_group)
    slot_groups.append(slot_group)
    orig_labels.append(o_lab)
    dest_labels.append(d_lab)
    flight_labels.append(f_lab)

superroot.append(root)


print("Test")
while True:

    # Show the currently selected flight (purple + its labels) for
    # FLIGHT_CHANGE seconds before deciding what happens next. Keeping the
    # "hide the old one" step below (either in the fetch branch or the
    # plain-rotation branch) instead of here means the currently displayed
    # flight stays on screen for the entire fetch, so nothing ever goes
    # blank while waiting on the network.
    if num_active > 0:
        slot_groups[current].hidden = False
        x, y = slot_x[current], slot_y[current]
        flightdots[x, y] = 2
        time.sleep(FLIGHT_CHANGE)

    if time.monotonic() - 10 > last_call:
        last_call = time.monotonic()

        try:
            flights = requests.get(DATA_SOURCE, timeout=10).json()["data"]
        except (OSError, RuntimeError, ValueError) as e:
            print("fetch failed:", e)
            flights = []

        if len(flights) > MAX_FLIGHTS:
            print("Too many flights (", len(flights), "), showing first", MAX_FLIGHTS)

        # New data is ready -- only now is it safe to clear the previous
        # cycle's dots/labels (using the OLD num_active/slot_x/slot_y). A
        # cleared pixel goes back to green if it's part of the receiver
        # marker, otherwise off.
        for i in range(num_active):
            x, y = slot_x[i], slot_y[i]
            flightdots[x, y] = 3 if (x, y) in receiver_pixels else 0

        num_active = min(len(flights), MAX_FLIGHTS)

        for i in range(MAX_FLIGHTS):
            if i < num_active:
                flight = flights[i]
                print(flight)
                pix_x, pix_y = get_loc(flight["latitude"], flight["longitude"])
                pix_x = min(31, max(0, pix_x))
                pix_y = min(31, max(0, pix_y))

                orig_labels[i].text = flight["orig_icao"]
                dest_labels[i].text = flight["dest_icao"]
                flight_text = flight["flight"] if flight["flight"] is not None else flight["registration"]
                flight_text = flight_text[:MAX_TEXT_LEN]
                flight_labels[i].text = flight_text + " " * (MAX_TEXT_LEN - len(flight_text))

                slot_x[i], slot_y[i] = pix_x, pix_y
                flightdots[pix_x, pix_y] = 1
            slot_groups[i].hidden = True

        del flights
        current = 0
    elif num_active > 0:
        slot_groups[current].hidden = True
        x, y = slot_x[current], slot_y[current]
        flightdots[x, y] = 1
        current = (current + 1) % num_active

    gc.collect()
