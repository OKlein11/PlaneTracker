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
from secrets import DATA_SOURCE,CENTER_LONG,CENTER_LAT,NE_CORNER,SW_CORNER


## CONSTANTS

FLIGHT_CHANGE = 5


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

def flight_loc_dot(x,y, bitmap):
    bitmap[x,y] = 1
    return [x,y]



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
root = displayio.Group()
display.root_group = superroot
last_call = time.monotonic()
flights = []
dots = []
root = displayio.Group()
flightdots = displayio.Bitmap(64,32,3)


palette = displayio.Palette(4)
palette[0] = 0x000000 # OFF
palette[1] = 0xFFFFFF # WHITE
palette[2] = 0xa102d6 # PURPLE
palette[3] = 0x00FF00 # GREEN
tile_grid = displayio.TileGrid(flightdots, pixel_shader=palette)
superroot.append(tile_grid)

print("TESTING")

flightdots[15,15] = 3
flightdots[15,16] = 3
flightdots[16,15] = 3
flightdots[16,16] = 3


superroot.append(root)


print("Test")
while True:

    if time.monotonic() - 10 > last_call:
        try:
            flights = requests.get(DATA_SOURCE, timeout=10).json()["data"]
            print(flights)
        except:
            flights = {}
        last_call = time.monotonic()
        root=displayio.Group()

        for dot in dots:
            if dot[0] in [15,16] and dot[1] in [15,16]:
                flightdots[dot[0],dot[1]] = 3
            else:
                flightdots[dot[0],dot[1]] = 0

        dots=[]




    for num,flight in enumerate(flights):
        if num >= 8:
            print("Too many flights, not enough mem")
            continue
        print(flight)
        pix_x, pix_y = get_loc(flight["latitude"],flight["longitude"])

        if pix_x > 31:
            pix_x = 31
        elif pix_x < 0:
            pix_x = 0

        if pix_y >31:
            pix_y = 31
        elif pix_y < 0:
            pix_y = 0


        root.append(displayio.Group())


        root[-1].append(orig_label(flight["orig_icao"]))
        root[-1].append(dest_label(flight["dest_icao"]))

        if flight["flight"] is not None:
            root[-1].append(flight_label(flight["flight"]))
        else:
            root[-1].append(flight_label(flight["registration"]))

        dots.append(flight_loc_dot(pix_x,pix_y,flightdots))

    for x in root:
        x.hidden=True

    superroot.pop(1)
    superroot.append(root)



    current_num = 0
    while current_num < len(root):
        root[current_num].hidden=False
        x,y = dots[current_num]
        flightdots[x,y]=2

        time.sleep(FLIGHT_CHANGE)
        root[current_num].hidden=True
        flightdots[x,y]=1

        current_num += 1
    if len(root) != 0:
        root[0].hidden = False
        x,y = dots[0]
        flightdots[x,y] = 2

    gc.collect()


