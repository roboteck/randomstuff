# # -----------------------------------------------------------------------------
# # Windows API
# # -----------------------------------------------------------------------------
# class Win32PrinterConfig(PrinterConfig):

#     def _default_printers(self):
#         if not PRINTER_AVAILABLE:
#             return []
#         try:
#             return [p[2] for p in win32print.EnumPrinters(
#                     win32print.PRINTER_ENUM_LOCAL)]
#         except Exception as e:
#             if 'RPC server is unavailable' in str(e):
#                 return []  # Ignore this error
#             raise


# class Win32PrinterConnection(PrinterConnection):
#     job = Instance(object)

#     def open(self):
#         p = win32print.OpenPrinter(self.transport.config.printer)
#         self.job = win32print.StartDocPrinter(
#             p, 1, ("Inkcut job", None, "RAW"))
#         win32print.StartPagePrinter(p)
#         self.printer = p

#         #: Sync
#         self.transport.connected = True
#         self.transport.protocol.connection_made()

#     def write(self, data):
#         super(Win32PrinterConnection, self).write(data)
#         win32print.WritePrinter(self.printer, bytearray(data,'ascii'))

#     def close(self):
#         p = self.printer
#         win32print.EndPagePrinter(p)
#         win32print.EndDocPrinter(p)
#         win32print.ClosePrinter(p)
#         #: Sync
#         self.transport.connected = False
#         self.transport.protocol.connection_lost()


# # -*- coding: utf-8 -*-
# """
# Created on Jul 25, 2015

# Thanks to Lex Wernars

# @author: jrm
# @author: lwernars
# """
# from inkcut.device.plugin import DeviceProtocol


# class GPGLProtocol(DeviceProtocol):
#     def connection_made(self):
#         self.write("H")

#     def move(self, x, y, z, absolute=True):
#         self.write("%s%i,%i"%('D' if z else 'M', x, y))

#     def set_velocity(self, v):
#         self.write('!%i' % v)

#     def set_force(self, f):
#         self.write("FX%i,1" % f)

#     def set_pen(self, p):
#         pass
####3# arr = bytearray(string, 'ascii')

import time
from warnings import warn

filenameep = "test_gpgl.txt"

class GPGL_Command(object):
    Name = "__GPGL_Command__"
    Command = ''

    def __init__(self, *args, **kw):
        self.args = args
        self.kw = kw

    def encode(self, msg=''):
        return "%s%s\x03" % (self.Command, msg)

    def decode(self, msg):
        pass

class Point(object):
    def __init__(self, *args, **kw):
        try: self.x = args[0]
        except: self.x = kw.get('x', 0)
        try: self.y = args[1]
        except: self.y = kw.get('y', 0)

    def __eq__(self, other):
        if other == None:
            return False
        other = Point(*list(other))
        return (self.x == other.x) and (self.y == other.y)
    def __sub__(self, other):
        other = Point(*list(other))
        return Point(self.x - other.x, self.y - other.y)
    def __add__(self, other):
        other = Point(*list(other))
        return Point(self.x + other.x, self.y + other.y)

    def __getitem__(self, idx):
        if idx == 0: return self.x
        if idx == 1: return self.y
        raise IndexError
    
    def __setitem__(self, idx, val):
        if idx == 0: self.x = val
        if idx == 1: self.y = val
        else: raise IndexError

    def __iter__(self):
        return iter([self.x, self.y])
    
    def __str__(self):
        return "%s,%s" % (self.x, self.y)

class Points(list):
    def __init__(self, *args, **kw):
        for arg in args:
            self.append(Point(*arg))

class Move(GPGL_Command):
    Command = 'M'
    
    def __init__(self, *args, **kw):
        self.position = Point(*args, **kw)
        super(Move, self).__init__(*args, **kw)

    def encode(self, msg=''):
        msg = "%s,%s" % (self.position.x, self.position.y)
        return super(Move, self).encode(msg)

class RelativeMove(Move):
    Command = 'O'

class Draw(GPGL_Command):
    Command = 'D'
    
    def __init__(self, *args, **kw):
        self.points = Points(*args, **kw)
        super(Draw, self).__init__(*args, **kw)
    
    def encode(self, msg=''):
        msg = [str(pt) for pt in self.points]
        msg = str.join(',', msg)
        return super(Draw, self).encode(msg)

class RelativeDraw(Draw):
    Command = 'E'

class Home(GPGL_Command):
    Command = 'H'

class Speed(GPGL_Command):
    Command = '!'

    def __init__(self, *args, **kw):
        self.speed = 1
        if args:
            self.speed = args[0]
        super(Speed, self).__init__(*args, **kw)

    def encode(self, msg=''):
        msg = str(self.speed)
        return super(Speed, self).encode(msg)

    def get_speed(self):
        return self._speed
    def set_speed(self, speed):
        self._speed = min(10, max(1, speed))
    speed = property(get_speed, set_speed)

class Media(GPGL_Command):
    Command = 'FW'

    def __init__(self, *args, **kw):
        try: self.media = args[0]
        except: self.media = kw.get('media', 300)
        super(Media, self).__init__(*args, **kw)

    def encode(self, msg=''):
        msg = str(self.media)
        return super(Media, self).encode(self.media)
    
    def set_media(self, val):
        self._media = min(300, max(100, val))
    def get_media(self):
        return self._media
    media = property(get_media, set_media)

class Pressure(GPGL_Command):
    Command = 'FX'

    def __init__(self, *args, **kw):
        try: self.pressure = args[0]
        except: self.pressure = kw.get('pressure', 0)
        super(Pressure, self).__init__(*args, **kw)

    def encode(self, msg=''):
        msg = str(self.pressure)
        return super(Pressure, self).encode(msg)

class Offset(GPGL_Command):
    Command = 'FC'

    def __init__(self, *args, **kw):
        try: self.offset = args[0]
        except: self.offset = kw.get('offset', 0)
        super(Offset, self).__init__(*args, **kw)

    def encode(self, msg=''):
        msg = str(self.offset)
        return super(Offset, self).encode(msg)


class Circle(GPGL_Command):
    Command = 'W'

    def __init__(self, *args, **kw):
        self.center = Point(*kw.get("center", (0, 0)))
        self.radius = kw.get("radius", 1)
        self.move = kw.get("move", False)
        super(Circle, self).__init__(*args, **kw)

    def three_points(self):
        pts = []
        pts.extend([self.center.x, self.center.y - self.radius])
        pts.extend([self.center.x, self.center.y + self.radius])
        pts.extend([self.center.x + self.radius, self.center.y])
        return pts
        
    def encode(self, msg=''):
        points = self.three_points()
        msg = [str(x) for x in points]
        msg = str.join(',', msg)
        msg =  super(Circle, self).encode(msg)
        if self.move:
            move = Move(self.center.x + self.radius, self.center.y)
            msg = move.encode() + msg
        return msg



class SilhouetteException(Exception):
    pass

class Silhouette(object):
    def __init__(self, **kw):
        self.vendor_id = kw.get('vendor_id', 0x0b4d)
        self.product_id = kw.get('product_id', None)
        self.pos = (0, 0)
        self._pressure = Pressure()
        self._speed = Speed()
        self._media = Media()
        self._offset = Offset()
        self._position = None
        self.ep_out = None
    
    def usbscan(self):
        args = {"find_all": True, "idVendor": self.vendor_id}
        if self.product_id:
            args["idProduct"] = self.product_id
        devs = usb.core.find(**args)
        devs = list(devs)
        if not devs:
            msg = "Can not find any devices with vendor_id == %s" % self.vendor_id
            raise SilhouetteException(msg)
            # raise Exception("Sorry, no numbers below zero")
         
        if len(devs) > 1:
            msg = "There are multiple devices that match vendor_id == %s, using the first one in the list." % self.vendor_id
            warn(msg)
        return devs[0]

    def connect(self):
        # self.dev = self.usbscan()
        # self.dev.reset()

        # # set the active configuration. With no arguments, the first
        # # configuration will be the active one
        # self.dev.set_configuration()

        # # get an endpoint instance
        # cfg = self.dev.get_active_configuration()

        # intf = cfg[(0,0)]

        # self.ep_out = usb.util.find_descriptor(intf,
        #     custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
        # assert self.ep_out is not None

        # self.ep_in = usb.util.find_descriptor(intf,
        #     custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
        # assert self.ep_in is not None

        # self.ep_intr_in = usb.util.find_descriptor(intf, 
        #         custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN and usb.util.endpoint_type(e.bEndpointAddress) == usb.util.ENDPOINT_TYPE_INTR)
        # assert self.ep_intr_in is not None
        
        # self.init()
        self.ep_out = open(filenameep, "a")
        # self.ep_out.write("test\n")
        # self.ep_out.close()

    def move(self, pos, rel=True):
        pos = Point(*list(pos))
        if self._position == pos:
            return
        if rel:
            rel_pos = pos - self._position
            move = RelativeMove(*rel_pos)
        else:
            move = Move(*pos)
        self.send(move)
        self._position = Point(*pos)

    def get_position(self):
        return self._position
    def set_position(self, pos):
        if self._position == None:
            self.move(pos, rel=False)
        else:
            self.move(pos)
    position = property(get_position, set_position)

    def draw(self, points):
        cmd = Draw(*points)
        self.send(cmd)
        self._position = cmd.points[-1]

    def init(self):
        self.write("\x1b\x04")

    def set_offset(self, offset):
        self._offset.offset = offset
        self.send(self._offset)
    def get_offset(self):
        return self._offset.offset
    offset = property(get_offset, set_offset)

    def set_speed(self, speed):
        self._speed.speed = speed
        self.send(self._speed)
    def get_speed(self):
        return self._speed.speed
    speed = property(get_speed, set_speed)

    def set_media(self, media):
        self._media.media = media
        self.send(self._media)
    def get_media(self):
        return self._media.media
    media = property(get_media, set_media)


    def set_pressure(self, pressure):
        self._pressure = Pressure(pressure)
        self.send(self._pressure)
    def get_pressure(self):
        return self._pressure.pressure
    pressure = property(get_pressure, set_pressure)

    def home(self):
        self.send(Home())

    @property
    def status(self):
        reslen = self.ep_out.write("\x1b\x05")
        resp = self.read(2)
        resp = list(resp)
        if len(resp) != 2:
            raise ValueError("Bad response to status request")
        (status_byte, magic_byte) = resp
        if magic_byte != 0x3:
            raise ValueError("Status magic byte does not equal 0x03 (0x%02x)" % resp[-1])
        if status_byte == 0x30:
            return "ready"
        if status_byte == 0x31:
            return "moving"
        if status_byte == 0x32:
            return "unloaded"
        return "unknown"
    
    @property
    def ready(self):
        return self.status == "ready"

    @property
    def moving(self):
        return self.status == "moving"

    @property
    def unloaded(self):
        return self.status == "unloaded"

    @property
    def version(self):
        self.write("FG")
        resp = self.read(1000)
        resp = str.join('', map(chr, resp))
        return resp
    
    def wait(self):
        while not self.ready:
            time.sleep(.1)

    def read(self, length=1):
        info = self.ep_in.read(length)
        return info

    def write(self, msg):
        # bufsize = self.ep_out.wMaxPacketSize
        # idx = 0
        # #print str.join(' ', ["%s (0x%02x)" % (x, ord(x)) for x in msg])
        # while idx < len(msg):
        #     submsg = msg[idx:idx + bufsize]
            # reslen = self.ep_out.write(submsg)
            #print "[%s:%s] %s" % (idx, idx + bufsize, len(msg))
            # assert reslen == len(submsg), "%s != %s" % (reslen, len(submsg))
            # idx += bufsize
            # if idx < len(msg):
            #     self.wait()
        
        # self.ep_out = open(filenameep, 'a')
        self.ep_out.write(msg)
        self.ep_out.close()

    def send(self, *commands, **kw):
        block = kw.get('block', True)
        for cmd in commands:
            self.write(cmd.encode())
            # if block: 
            #     self.wait()


if __name__ == '__main__':
    _cutter = None
    _cutter = Silhouette()
    _cutter.connect()
    # _cutter.speed = 1
    _cutter.home()