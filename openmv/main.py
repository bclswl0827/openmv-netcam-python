import sensor, ustruct
from pyb import USB_VCP

keyword = 'snap'

usb = USB_VCP()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.VGA)
sensor.skip_frames(time=2000)

while (True):
    cmd = usb.recv(len(keyword), timeout=1000)
    if (cmd == keyword.encode()):
        img = sensor.snapshot().compress()
        usb.send(ustruct.pack("<L", img.size()))
        usb.send(img)
