import busio
import time
import board
import displayio
import digitalio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1106
import simpleio
import adafruit_rgbled
from analogio import AnalogIn
from rainbowio import colorwheel

displayio.release_displays()

spi = busio.SPI(board.GP10, board.GP11)
display_bus = displayio.FourWire(
    spi,
    command=board.GP20,
    chip_select=board.GP21,
    reset=board.GP22,
    baudrate=1000000,
)

WIDTH = 128
HEIGHT = 64
BORDER = 5
display = adafruit_displayio_sh1106.SH1106(display_bus, width=WIDTH, height=HEIGHT, rotation=180)

# Make the display context
splash = displayio.Group()
display.show(splash)

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
)
splash.append(inner_sprite)

# Draw a label
text = "Hello World!"
text_area = label.Label(
    terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=HEIGHT // 2 - 1
)
splash.append(text_area)

button= digitalio.DigitalInOut(board.GP12)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

charging = digitalio.DigitalInOut(board.GP13)
charging.direction = digitalio.Direction.INPUT
charging.pull = digitalio.Pull.DOWN

# Battery Analog
analog_bat = AnalogIn(board.GP27)

RGBled1 = adafruit_rgbled.RGBLED(board.GP7, board.GP8, board.GP9, invert_pwm=True)

# Voltage Func
def get_voltage(pin):
    return ((pin.value * 3.3) / 65536)*2

while True:
    text_area.text = str(get_voltage(analog_bat))
    if button.value is False:
        text_area.text = "Play tune"
        simpleio.tone(board.GP15, 330, duration=0.25)
        simpleio.tone(board.GP15, 349, duration=0.25)
        simpleio.tone(board.GP15, 392, duration=0.25)
        simpleio.tone(board.GP15, 523, duration=0.5)
    else:
        for i in range(255):
            i = (i + 1) % 256
            RGBled1.color = colorwheel(i)
            time.sleep(0.01)
    pass