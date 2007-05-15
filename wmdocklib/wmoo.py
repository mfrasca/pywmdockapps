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
        self._events = []
        self._sleep = 0.1
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

    def update(self):
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
