class MyRange:
    def __init__(self, start, stop=None, step=1):
        if stop is None:
            start, stop = 0, start
        if step == 0:
            raise ValueError("step cannot be 0")
        self.start = start
        self.stop = stop
        self.step = step
    
    def __iter__(self):
        current = self.start
        while (self.step > 0 and current < self.stop) or (self.step < 0 and current > self.stop):
            yield current
            current += self.step
    
    def __len__(self):
        return max(0, (self.stop - self.start + (self.step - (self.step > 0))) // self.step)
    
    def __getitem__(self, index):
        if index < 0 or index >= len(self):
            raise IndexError("range object index out of range")
        return self.start + index * self.step