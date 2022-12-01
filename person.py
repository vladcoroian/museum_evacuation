class Person:
    def __init__(self, id, rate: float = 1.0, strategy: float = .7, loc: tuple = None):
        self.id = id
        self.rate = rate
        self.strategy = strategy
        self.exit_time = 0
        self.safe = False
        self.alive = True
        self.loc = tuple(loc)

    def move(self, nbrs, rv=None):
        nbrs = [(loc, attrs) for loc, attrs in nbrs if not (attrs['F'] or attrs['W'])]
        if not nbrs:
            return None
        loc, attrs = min(nbrs, key=lambda tup: tup[1]['distS'])
        self.loc = loc
        if attrs['S']:
            self.safe = True

        return loc
