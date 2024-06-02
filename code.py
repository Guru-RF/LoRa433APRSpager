import asyncio
import binascii
import random
import time

import adafruit_displayio_sh1106
import adafruit_rfm9x
import adafruit_rgbled
import board
import busio
import displayio
import pwmio
import rtc
import terminalio
from adafruit_display_shapes.line import Line
from adafruit_display_text.bitmap_label import Label
from adafruit_display_text.scrolling_label import ScrollingLabel
from analogio import AnalogIn
from digitalio import DigitalInOut, Direction, Pull
from displayio import FourWire
from microcontroller import watchdog as w
from watchdog import WatchDogMode

import config


# Format Time
def _format_datetime(datetime):
    return "{:02}/{:02}/{:02} {:02}:{:02}".format(
        datetime.tm_mon,
        datetime.tm_mday,
        datetime.tm_year % 100,
        datetime.tm_hour,
        datetime.tm_min,
    )


def _format_datetime_short(datetime):
    return "{:02}/{:02} {:02}:{:02}".format(
        datetime.tm_mday,
        datetime.tm_mon,
        datetime.tm_hour,
        datetime.tm_min,
    )


# Voltage Func
def get_voltage(pin):
    return ((pin.value * 3.3) / 65536) * 2


def purple(data):
    stamp = "{}".format(_format_datetime(time.localtime()))
    return (
        "\033[K\x1b[38;5;104m["
        + str(stamp)
        + "] "
        + config.call
        + " "
        + data
        + "\x1b[0m"
    )


def green(data):
    stamp = "{}".format(_format_datetime(time.localtime()))
    return (
        "\033[K\x1b[38;5;112m["
        + str(stamp)
        + "] "
        + config.call
        + " "
        + data
        + "\x1b[0m"
    )


def blue(data):
    stamp = "{}".format(_format_datetime(time.localtime()))
    return (
        "\033[K\x1b[38;5;14m["
        + str(stamp)
        + "] "
        + config.call
        + " "
        + data
        + "\x1b[0m"
    )


def yellow(data):
    return "\033[K\x1b[38;5;220m" + data + "\x1b[0m"


def red(data):
    stamp = "{}".format(_format_datetime(time.localtime()))
    return (
        "\033[K\x1b[1;5;31m[" + str(stamp) + "] " + config.call + " " + data + "\x1b[0m"
    )


def bgred(data):
    stamp = "{}".format(_format_datetime(time.localtime()))
    return "\033[K\x1b[41m[" + str(stamp) + "] " + config.call + data + "\x1b[0m"


# setup buzzer (set duty cycle to ON to sound)
buzzer = pwmio.PWMOut(board.GP15, variable_frequency=True)
buzzer.frequency = 880

displayio.release_displays()

spi = busio.SPI(board.GP10, board.GP11)
display_bus = FourWire(
    spi,
    command=board.GP20,
    chip_select=board.GP21,
    reset=board.GP22,
    baudrate=1000000,
)


WIDTH = 128
HEIGHT = 64
BORDER = 5
display = adafruit_displayio_sh1106.SH1106(
    display_bus,
    width=WIDTH + 2,
    height=HEIGHT,
    rotation=180,
)


# Make the display context
splash = displayio.Group()
display.root_group = splash

# color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
# color_palette = displayio.Palette(1)
# color_palette[0] = 0xFFFFFF  # White
#
# bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
# splash.append(bg_sprite)
#
## Draw a smaller inner rectangle
# inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
# inner_palette = displayio.Palette(1)
# inner_palette[0] = 0x000000  # Black
# inner_sprite = displayio.TileGrid(
#    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
# )
# splash.append(inner_sprite)

text = "00/00"
aprsMessageNr = Label(terminalio.FONT, text=text, max_charactrters=20, animate_time=0)
aprsMessageNr.x = 3
aprsMessageNr.y = 20
splash.append(aprsMessageNr)

text = "Messages"
aprsUIInfo = Label(terminalio.FONT, text=text, max_charactrters=20, animate_time=0)
aprsUIInfo.x = 3
aprsUIInfo.y = 30
splash.append(aprsUIInfo)

text = ""
aprsMessageCall = Label(terminalio.FONT, text=text, max_charactrters=20, animate_time=0)
aprsMessageCall.x = 60
aprsMessageCall.y = 20
splash.append(aprsMessageCall)

text = ""
aprsMessageTimeStamp = Label(
    terminalio.FONT, text=text, max_charactrters=20, animate_time=0
)
aprsMessageTimeStamp.x = 60
aprsMessageTimeStamp.y = 30
splash.append(aprsMessageTimeStamp)

text = "Waiting for messages ..."
aprsMessage = ScrollingLabel(
    terminalio.FONT, text=text, max_characters=20, animate_time=0.3
)
aprsMessage.x = 4
aprsMessage.y = 43
splash.append(aprsMessage)

## APRSGateway
text = "{:9}".format("NO SIGNAL")
aprsGateway = Label(terminalio.FONT, text=text, max_characters=18, animate_time=0)
aprsGateway.x = 3
aprsGateway.y = 7
splash.append(aprsGateway)

## APRSSNR
text = "SNR:0.00"
aprsSNR = Label(terminalio.FONT, text=text, max_characters=18, animate_time=0)
aprsSNR.x = 78
aprsSNR.y = 7
splash.append(aprsSNR)

## Battery
text = "B:99%"
batteryLevel = Label(terminalio.FONT, text=text, max_characters=18, animate_time=0)
batteryLevel.x = 3
batteryLevel.y = 57
splash.append(batteryLevel)

## Time
text = "DD/MM/YY HH:MM"
displayTime = Label(terminalio.FONT, text=text, max_characters=20, animate_time=0.4)
displayTime.x = 42
displayTime.y = 57
splash.append(displayTime)

splash.append(Line(0, 0, 270, 0, 0xFFFFFF))
splash.append(Line(0, 13, 270, 13, 0xFFFFFF))
splash.append(Line(127, 0, 127, 63, 0xFFFFFF))
splash.append(Line(57, 13, 57, 36, 0xFFFFFF))
splash.append(Line(0, 0, 0, 63, 0xFFFFFF))
splash.append(Line(0, 36, 270, 36, 0xFFFFFF))
splash.append(Line(0, 50, 270, 50, 0xFFFFFF))
splash.append(Line(0, 63, 270, 63, 0xFFFFFF))

button = DigitalInOut(board.GP12)
button.direction = Direction.INPUT
button.pull = Pull.UP

charging = DigitalInOut(board.GP13)
charging.direction = Direction.INPUT
charging.pull = Pull.DOWN

# Battery Analog
analog_bat = AnalogIn(board.GP27)

RGBled1 = adafruit_rgbled.RGBLED(board.GP7, board.GP8, board.GP9, invert_pwm=True)


# text_area.text = "APRSiGate"


# while True:
#    text_area.text = str(get_voltage(analog_bat))
#    if button.value is False:
#        text_area.text = "Play tune"
#        simpleio.tone(board.GP15, 330, duration=0.25)
#        simpleio.tone(board.GP15, 349, duration=0.25)
#        simpleio.tone(board.GP15, 392, duration=0.25)
#        simpleio.tone(board.GP15, 523, duration=0.5)
#    else:
#        for i in range(255):
#            i = (i + 1) % 256
#            RGBled1.color = colorwheel(i)
#            time.sleep(0.01)
#    pass

# configure watchdog
w.timeout = 5
w.mode = WatchDogMode.RESET
w.feed()

loraTimeout = 15


async def playTone(loop, type="default"):
    OFF = 0
    ON = 2**15
    global buzzer
    if type == "default":
        for x in range(40):
            buzzer.frequency = 330 + (x * 15)
            buzzer.duty_cycle = ON
            await asyncio.sleep(0.02)
            buzzer.duty_cycle = OFF
            buzzer.frequency = 580 + (x * 15)
            buzzer.duty_cycle = ON
            await asyncio.sleep(0.02)
            buzzer.duty_cycle = OFF
    if type == "beacon":
        buzzer.frequency = 440
        buzzer.duty_cycle = ON
        await asyncio.sleep(0.02)
        buzzer.duty_cycle = OFF
        buzzer.frequency = 880
        buzzer.duty_cycle = ON
        await asyncio.sleep(0.02)
        buzzer.duty_cycle = OFF


async def displayRunner(loop):
    global aprsMessage, displayTime
    while True:
        await asyncio.sleep(0)
        aprsMessage.update()
        if displayTime.text != "{}".format(_format_datetime(time.localtime())):
            displayTime.text = "{}".format(_format_datetime(time.localtime()))


async def loraRunner(loop):
    global \
        w, \
        aprsMessage, \
        aprsMessageCall, \
        aprsMessageTimeStamp, \
        aprsMessageNr, \
        aprsUIInfo, \
        aprsGateway
    # Continuously receives LoRa packets and forwards valid APRS packets
    # via WiFi. Configures LoRa radio, prints status messages, handles
    # exceptions, creates asyncio tasks to process packets.
    # LoRa APRS frequency
    RADIO_FREQ_MHZ = 433.775
    CS = DigitalInOut(board.GP0)
    RESET = DigitalInOut(board.GP1)
    spi = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)
    rfm9x = adafruit_rfm9x.RFM9x(
        spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000, agc=False, crc=True
    )

    nrMessages = 0

    # tx msg buffer
    ackmsgs = []

    while True:
        await asyncio.sleep(0)
        w.feed()
        timeout = int(loraTimeout) + random.randint(1, 9)
        print(
            purple(f"loraRunner: Waiting for lora APRS packet timeout:{timeout} ...\r"),
            end="",
        )
        startime = time.monotonic()
        packet = await rfm9x.areceive(w, with_header=True, timeout=timeout)
        if packet is not None:
            if packet[:3] == (b"<\xff\x01"):
                try:
                    rawdata = bytes(packet[3:]).decode("utf-8")
                    print(
                        green(
                            f"loraRunner: RX: RSSI:{rfm9x.last_rssi} SNR:{rfm9x.last_snr} Data:{rawdata}"
                        )
                    )
                    # only aprs messages
                    if "::" in rawdata:
                        aprsdata = rawdata.split("::", 1)
                        # only text messages
                        if aprsdata[1].count(":") == 2:
                            gateway = (rawdata.split(">", 1))[0]
                            aprsmessage = aprsdata[1].split(":", 2)
                            fromcall = aprsmessage[0]
                            tocall = aprsmessage[1].strip()
                            message = aprsmessage[2]
                            acknr = ""
                            if "{" in aprsmessage[2]:
                                message, acknr = aprsmessage[2].split("{", 1)
                            if tocall is config.call:
                                # asyncio.create_task(playTone(loop))
                                nrMessages += 1
                                aprsMessage.text = "> {} | ".format(message)
                                aprsMessageNr.text = "{:02}/{:02}".format(
                                    nrMessages, nrMessages
                                )
                                aprsMessageCall.text = "@ {:9}".format(fromcall)
                                aprsMessageTimeStamp.text = "{}".format(
                                    _format_datetime_short(time.localtime())
                                )
                                aprsSNR.text = "SNR:{:04}".format(str(rfm9x.last_snr))
                                aprsGateway.text = "{:9}".format(gateway)

                            ackmessage = ""
                            if acknr != "":
                                ackmessage = "{}>APRFGT::{:9}:ack{}".format(
                                    config.call, fromcall, acknr
                                )
                                ackmsgs.append(ackmessage)

                            print(
                                yellow(
                                    f"loraRunner: MSG: FROM:{fromcall} TO:{tocall} MSG:{message} ACK:{acknr} ACKMSG:{ackmessage}"
                                )
                            )

                        elif aprsdata[1].count(":") == 1:
                            aprsmessage = aprsdata[1].split(":", 1)
                            tocall = aprsmessage[0]
                            gateway = (rawdata.split(">", 1))[0]
                            aprstime = aprsmessage[1].strip()
                            if tocall == "APRFGD":
                                asyncio.create_task(playTone(loop, "beacon"))
                                aprsSNR.text = "SNR:{:04}".format(str(rfm9x.last_snr))
                                aprsGateway.text = "{:9}".format(gateway)
                                rtc.RTC().datetime = time.localtime(int(aprstime))

                                print()
                                print(
                                    green(
                                        f"loraRunner: BEACON: FROM:{gateway} TO:{tocall} TIME:{aprstime}"
                                    )
                                )
                    await asyncio.sleep(0)
                except Exception as error:
                    print(bgred(f"loraRunner: An exception occurred: {error}"))
                    print(purple("loraRunner: Lost Packet, unable to decode, skipping"))
                    continue

        if timeout == int(time.monotonic() - startime):
            if len(ackmsgs) != 0:
                while len(ackmsgs) != 0:
                    w.feed()
                    packet = ackmsgs.pop(0)
                    print()
                    print(red(f"loraRunner: TX: {packet}"))
                    await rfm9x.asend(
                        bytes("{}".format("<"), "UTF-8")
                        + binascii.unhexlify("FF")
                        + binascii.unhexlify("01")
                        + bytes("{}".format(packet), "UTF-8"),
                    )
                    w.feed()


async def main():
    # Create asyncio tasks to run the LoRa receiver, APRS message feed,
    # and iGate announcement in parallel. Gather the tasks and wait for
    # them to complete wich will never happen ;)
    loop = asyncio.get_event_loop()
    loraL = asyncio.create_task(loraRunner(loop))
    loraD = asyncio.create_task(displayRunner(loop))
    await asyncio.gather(loraL, loraD)


asyncio.run(main())
