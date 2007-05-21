import sys, time
import pywmhelpers

debug = 0

class Application:
    def __init__(self, *args, **kwargs):
        """initializes the object

        _events is a list of tuples (type, key, area, callback)
          'type' <- ['buttonpress', 'buttonrelease', 'keypress'],
          'callback': the function to which the event should be passed.
          'key': the utf-8 character or the mouse button number,
          'area': if the pointer is here, the event is considered,
        
        """
        self._elements = {}
        self._events = []
        self._sleep = 0.1
        self._cycle = 0
        self._offset_x = self._offset_y = 3

        self._char_width, self._char_height = pywmhelpers.initPixmap(*args, **kwargs)
        pywmhelpers.openXwindow(sys.argv, 64, 64)
        pass

    def putString(self, x, y, string):
        pywmhelpers.addString(string, x, y,
                              self._offset_x, self._offset_y,
                              self._char_width, self._char_height)

    def putPattern(self, sourceX, sourceY, width, height, targetX, targetY):
        pywmhelpers.copyXPMArea(sourceX, sourceY+64, width, height,
                                targetX, targetY)

    def addLabel(self, labelId, orig, size=None, text=None):
        """a label is a tuple with a
        text: string; mutable
        viewport: (orig: int, int, size: int, int); inmutable
        pixmap: drawable; not user mutable, large enough to contain the text

        if size is not given, it is inferred from text.
        """
        if size is None:
            size = (self._char_width * len(text), self._char_height)
        pixmapwidth = self._char_width * len(text)
        import pywmgeneral
        labelPixmap = pywmgeneral.Drawable(pixmapwidth, self._char_height)
        self._elements[labelId] = [orig, size, pixmapwidth, 0, labelPixmap]
        self.setLabelText(labelId, text)

    def setLabelText(self, labelId, text):
        """updates the drawable associated with labelId
        """
        (orig_x,orig_y), (size_x, size_y), width, offset, pixmap = self._elements[labelId]
        newwidth = self._char_width * len(text)
        if newwidth > width:
            import pywmgeneral
            pixmap = pywmgeneral.Drawable(newwidth, self._char_height)
            self._elements[labelId][4] = pixmap
        self._elements[labelId][2] = newwidth
        self._elements[labelId][3] = 0
        pixmap.xClear()
        pywmhelpers.addString(text, 0, 0, drawable=pixmap)
        pixmap.xCopyAreaToWindow(0, 0, size_x, size_y, orig_x, orig_y)
    
    def update(self):
        for labelId in self._elements:
            (orig_x,orig_y), (size_x, size_y), width, offset, pixmap = self._elements[labelId]
            if size_x < width:
                pixmap.xCopyAreaToWindow(offset, 0, size_x, size_y, orig_x, orig_y)
                if offset == width:
                    offset = -size_x
                else:
                    offset += 1
                self._elements[labelId][3] = offset
                
        pass

    def redraw(self):
        self.update()
        pywmhelpers.redraw()

    def addHandler(self):
        """adds a signal handler.

        if the application receives the signal, the handler is called.

        notice that the operating system does not know 'permanent' handlers,
        handlers are called once and that is it.  the addHandler function
        takes care that the call is repeated each time the signal is
        received (repeated signals received during the handling of the
        previous signal will be lost, though).
        """
        pass

    def addCallback(self, callback, type=None, key=None, area=None ):
        """the callback will be called during the eventLoop if the event
        matches the requirements on the type of the event, the key and the
        area where the event took place.  remind that events are mostly
        mouse or keyboard event.  all fields may be left to their 'None'
        default value, in which case the callback is activated on any event.
        """
        if area is not None and len(area) is not 4:
            area = None
        self._events.append( (type, key, area, callback,) )
        pass
    
    def run(self):
        """this contains the eventLoop.  events are examined and if a
        callback has been registered, it is called, passing it the event as
        argument.
        """
        while 1:
            event = pywmhelpers.getEvent()
            while not event is None:
                if event['type'] == 'destroynotify':
                    sys.exit(0)

                for evtype, key, area, callback in self._events:
                    if evtype is not None and evtype != event['type']: continue
                    if key is not None and key != event['button']: continue
                    if area is not None:
                        if not area[0] <= event['x'] <= area[2]: continue
                        if not area[1] <= event['y'] <= area[3]: continue

                    callback(event)
                    
                event = pywmhelpers.getEvent()
            self.redraw()
            time.sleep(self._sleep)
            
    pass
