import sys, time
import pywmhelpers

debug = 0

LEFT = 0
CENTRE = 1
RIGHT = 2

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
        self._buttons = {}
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

    def addLabel(self, labelId, orig, size=None, text='', align=LEFT):
        """a label is a tuple with a
        text: string; mutable
        viewport: (orig: int, int, size: int, int); inmutable
        pixmap: drawable; not user mutable, large enough to contain the text
        align: one of LEFT, CENTRE, RIGHT

        if size is not given, it is inferred from text.
        """
        if size is None:
            size = (self._char_width * len(text), self._char_height)
        pixmapwidth = max(self._char_width * len(text), size[0])
        import pywmgeneral
        labelPixmap = pywmgeneral.Drawable(pixmapwidth, self._char_height)
        self._elements[labelId] = {
            'orig': orig,
            'size': size,
            'pixw': pixmapwidth,
            'offset': 0,
            'pixmap': labelPixmap,
            'align': align}
        self.setLabelText(labelId, text)

    def setLabelText(self, labelId, text):
        """updates the drawable associated with labelId
        """
        lbl = self._elements[labelId]
        (orig_x,orig_y) = lbl['orig']
        (size_x, size_y) = lbl['size']
        newwidth = self._char_width * len(text)
        if newwidth > lbl['pixw']:
            import pywmgeneral
            lbl['pixmap'] = pywmgeneral.Drawable(newwidth, self._char_height)
        lbl['pixw'] = newwidth
        lbl['offset'] = 0
        lbl['pixmap'].xClear()
        lbl['pixmap'].xCopyAreaToWindow(0, 0, size_x, size_y, orig_x, orig_y)
        w = pywmhelpers.addString(text, 0, 0, drawable=lbl['pixmap'])
        dx = 0
        if w < size_x:
            spare = size_x - w
            if lbl['align'] == RIGHT:
                dx = spare
            elif lbl['align'] == CENTRE:
                dx = int(spare/2)
        else:
            w = size_x
            
        lbl['pixmap'].xCopyAreaToWindow(0, 0, w, size_y, orig_x+dx, orig_y)

    def addButton(self, buttonId, orig, size,
                  callback1, callback2=None, callback3=None,
                  pattern=None):
        """adds an area sensitive to the click of the mouse buttons

        the graphical appearance can be specified in the pattern or left as
        in the background.  in both cases, it can later be modified by
        calling setButtonPattern
        """

        orig_x, orig_y = orig
        dx, dy = size
        area = (orig_x, orig_y, orig_x + dx, orig_y + dy)
        self.addCallback(callback1, 'buttonrelease', area=area)
        if callback2 is not None:
            self.addCallback(callback2, 'buttonrelease', area=area)
        if callback3 is not None:
            self.addCallback(callback3, 'buttonrelease', area=area)
        self._buttons[buttonId] = (orig, size)
        if pattern is not None:
            self.setButtonPattern(buttonId, pattern)

    def setButtonPattern(self, buttonId, patternOrig):
        """paints the pattern on top of the button
        """

        (x, y), (w, h) = self._buttons[buttonId]
        pywmhelpers.copyXPMArea(patternOrig[0], patternOrig[1] + 64, w, h, x, y)
    
    def update(self):
        pass

    def redraw(self):
        for lbl in self._elements.values():
            (orig_x,orig_y) = lbl['orig']
            (size_x, size_y) = lbl['size']
            if lbl['size'][0] < lbl['pixw']:
                lbl['pixmap'].xCopyAreaToWindow(lbl['offset'], 0, size_x, size_y, orig_x, orig_y)
                if lbl['offset'] == lbl['pixw']:
                    lbl['offset'] = -size_x
                else:
                    lbl['offset'] += 1
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
                    if area is not None and 'x' in event:
                        if not area[0] <= event['x'] <= area[2]: continue
                        if not area[1] <= event['y'] <= area[3]: continue

                    callback(event)
                    
                event = pywmhelpers.getEvent()
            self.redraw()
            time.sleep(self._sleep)
            
    pass
