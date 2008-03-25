import sys, time
import pywmhelpers

debug = 0

LEFT = 0
CENTRE = 1
RIGHT = 2

class Widget:
    """
    a widget is a graphical object able to display itself.

    a wiget stores its graphical representation in a Drawable.  it gets the
    chance to update its Drawable periodically, since the application will
    scan all its widgets and call their 'update' method.

    a callback can be associated to a widget during its creation.  all that
    happens behind the scenes is that the callback is registered on the area
    of the widget, but it is not really directly associated to it.
    """
    def __init__(self):
        '''do not call ancestor constructor in derived classes!'''
        raise NotImplementedError('Widget is not instantiable')
    def update(self):
        pass
    pass

class Label(Widget):
        
    def __init__(self, container, orig, size=None, text='', align=LEFT):
        """a label is a tuple with...
        text: string; mutable
        viewport: (orig: int, int, size: int, int); inmutable
        pixmap: drawable; not user mutable, large enough to contain the text
        align: one of LEFT, CENTRE, RIGHT

        if size is not given, it is inferred from text.
        """
        # print container, orig, size, text, align
        if size is None:
            size = (container._char_width * len(text), container._char_height)
        pixmapwidth = max(container._char_width * len(text), size[0])
        import pywmgeneral
        labelPixmap = pywmgeneral.Drawable(pixmapwidth, container._char_height)
        self.orig = orig
        self.size = size
        self.pixw = pixmapwidth
        self.offset = 0
        self.pixmap = labelPixmap
        self.align = align
        self.container = container
        self.setText(text)

    def update(self):
        (orig_x,orig_y) = self.orig
        (size_x, size_y) = self.size
        if self.size[0] < self.pixw:
            self.pixmap.xCopyAreaToWindow(self.offset, 0, size_x, size_y, orig_x, orig_y)
            if self.offset == self.pixw:
                self.offset = -size_x
            else:
                self.offset += 1

    def setText(self, text):
        (orig_x,orig_y) = self.orig
        (size_x, size_y) = self.size
        newwidth = self.container._char_width * len(text)
        if newwidth > self.pixw:
            import pywmgeneral
            self.pixmap = pywmgeneral.Drawable(newwidth, self.container._char_height)
        self.pixw = newwidth
        self.offset = 0
        self.pixmap.xClear()
        self.pixmap.xCopyAreaToWindow(0, 0, size_x, size_y, orig_x, orig_y)
        w = pywmhelpers.addString(text, 0, 0, drawable=self.pixmap)
        dx = 0
        if w < size_x:
            spare = size_x - w
            if self.align == RIGHT:
                dx = spare
            elif self.align == CENTRE:
                dx = int(spare/2)
        else:
            w = size_x
        self.pixmap.xCopyAreaToWindow(0, 0, w, size_y, orig_x+dx, orig_y)

class Button(Widget):

    def __init__(self, container, orig, size,
                  callback1, callback2=None, callback3=None,
                  pattern=None):
        """adds an area sensitive to the click of the mouse buttons

        the graphical appearance can be specified in the pattern or left as
        in the background.  in both cases, it can later be modified by
        calling setButtonPattern
        """
        # print container, orig, size, callback1, callback2, callback3, pattern

        orig_x, orig_y = orig
        dx, dy = size
        area = (orig_x, orig_y, orig_x + dx, orig_y + dy)
        container.addCallback(callback1, 'buttonrelease', area=area)
        if callback2 is not None:
            container.addCallback(callback2, 'buttonrelease', area=area)
        if callback3 is not None:
            container.addCallback(callback3, 'buttonrelease', area=area)
        self.area = (orig_x, orig_y, dx, dy)
        if pattern is not None:
            self.setPattern(pattern)

    def setPattern(self, patternOrig):
        """paints the pattern on top of the button
        """

        (x, y, w, h) = self.area
        pywmhelpers.copyXPMArea(patternOrig[0], patternOrig[1] + 64, w, h, x, y)
    pass

BOUNCE = 0
BAR = 1
TSIZE = 2
TUSED = 3
TFREE = 4
TPERCENT = 5
EMPTY = 6

HORIZONTAL = 0
VERTICAL = 1

class ProgressBar(Widget):
    """a bit more generic than a progress bar...

    it shows as a progress bar, a percentage, an absolute quantity or a
    custom pixmap.

    properties (all are mutable)
    capacity: defaults to 1
    used: how much of capacity used.
    style: one of [bar, bounce, (t-size, t-used, t-free, t-percent, empty)]
    orientation: [horizontal, vertical]
    fg, bg: the colours for the bar.
    
    """

    def __init__(self, container, orig, size, style=BAR,
                 orientation=HORIZONTAL):
        pass

    def showCacheLevel(self):
        if self._buffering:
            self._cacheLevel += 1
            if self._cacheLevel >= 25:
                self._cacheLevel -= 25
            for i in range(-1, 25):
                if abs(i - self._cacheLevel) <= 1:
                    self.putPattern(54, self._buffering, 5, 1, 54, 51-i)
                else:
                    self.putPattern(54, 0, 5, 1, 54, 51-i)
        else:
            if self._flash:
                colour = self._colour = 3 - self._colour
                self._flash = max(0, self._flash - 1)
            else:
                colour = 2
            for i in range(-1, 25):
                if (i*4 < self._cacheLevel) or self._flash:
                    self.putPattern(54, colour, 5, 1, 54, 51-i)
                else:
                    self.putPattern(54, 0, 5, 1, 54, 51-i)

class Application:
    def __init__(self, *args, **kwargs):
        """initializes the object

        _events is a list of tuples (type, key, area, callback)
          'type' <- ['buttonpress', 'buttonrelease', 'keypress'],
          'callback': the function to which the event should be passed.
          'key': the utf-8 character or the mouse button number,
          'area': if the pointer is here, the event is considered,
        
        """
        self._widgets = {}
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

    def addWidget(self, widgetId, widgetClass, *args, **kwargs):
        # print widgetId, widgetClass, args, kwargs
        self._widgets[widgetId] = widgetClass(self, *args, **kwargs)

    def widget(self, name):
        return self._widgets[name]

    def __getitem__(self, key):
        return self._widgets[key]
    
    def update(self):
        pass

    def redraw(self):
        for item in self._widgets.values():
            item.update()
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
