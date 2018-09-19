import sys

try:
    _ = xrange
except NameError:
    xrange = range


class Params(dict):

    def __init__(self, input_=None, **kwargs):
        
        self._max_idx = 0

        if input_:
            self.update_or_extend(input_)
        if kwargs:
            self.update(kwargs)

    @classmethod
    def from_stack(cls, depth=0):
        self = cls()
        self.update_from_stack(depth + 1)
        return self

    def append(self, x):
        self[self._max_idx] = x
        self._max_idx += 1

    def extend(self, x):
        for y in x:
            self.append(y)

    def update_or_extend(self, x):
        if isinstance(x, (tuple, list)):
            self.extend(x)
        elif isinstance(x, dict):
            self.update(x)
        else:
            raise TypeError("update_or_extend takes list, tuple, or dict.")
    
    def update_from_stack(self, depth):
        frame = sys._getframe(depth + 1)
        self.update(frame.f_globals)
        self.update(frame.f_locals)

    def __getitem__(self, key):

        super_ = super(Params, self).__getitem__
        if not isinstance(key, slice):
            return super_(key)

        i = 0 if key.start is None else key.start
        stop = key.stop
        step = key.step or 1

        out = []
        while stop is None or i < stop:
            try:
                out.append(super_(i))
            except KeyError:
                break
            i += step
        
        return out




