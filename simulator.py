import simulus
import random
from person import Person
from bottleneck import Bottleneck
from floorparse import FloorParser

class Simulator:
    sim = None
    graph = None  # dictionary (x,y) --> attributes
    gui = False
    r = None
    c = None
    numpeople = 0
    numdead = 0
    numsafe = 0
    nummoving = 0
    bottlenecks = dict()
    fires = set()
    people = []
    exit_times = []
    avg_exit = 0  # tracks sum first, then we divide

    def __init__(self, input, n, location_sampler=random.sample,
                 strategy_generator=lambda: random.uniform(.5, 1.),
                 rate_generator=lambda: abs(random.normalvariate(1, .5)),
                 person_mover=random.uniform, fire_mover=random.sample,
                 fire_rate=2, bottleneck_delay=1, animation_delay=.1,
                 verbose=False,
                 **kwargs):
        self.sim = simulus.simulator()
        self.parser = FloorParser()
        self.animation_delay = animation_delay
        self.verbose = verbose

        with open(input, 'r') as f:
            self.graph = self.parser.parse(f.read())
        self.numpeople = n

        self.location_sampler = location_sampler
        self.strategy_generator = strategy_generator
        self.rate_generator = rate_generator
        self.person_mover = person_mover
        self.fire_mover = fire_mover

        self.fire_rate = fire_rate
        self.bottleneck_delay = bottleneck_delay
        self.kwargs = kwargs

        self.setup()

    def precompute(self):
        graph = self.graph

        def bfs(target, pos):
            if graph[pos]['W']:
                return float('inf')
            q = [(pos, 0)]
            visited = set()
            while q:
                node, dist = q.pop()
                if node in visited:
                    continue
                visited.add(node)

                node = graph[node]
                if node['W'] or node['F']:
                    continue
                if node[target]:
                    return dist

                for n in node['nbrs']:
                    if n in visited:
                        continue
                    q = [(n, dist+1)] + q
            return float('inf')

        for loc in graph:
            graph[loc]['distF'] = bfs('F', loc)
            graph[loc]['distS'] = bfs('S', loc)

        self.graph = dict(graph.items())

        return self.graph

    def setup(self):
        self.precompute()
        av_locs = []
        bottleneck_locs = []
        fire_locs = []
        r, c = 0, 0
        for loc, attrs in self.graph.items():
            r = max(r, loc[0])
            c = max(c, loc[1])
            if attrs['P']:
                av_locs += [loc]
            elif attrs['B']:
                bottleneck_locs += [loc]
            elif attrs['F']:
                fire_locs += [loc]

        assert len(av_locs) > 0, 'ERR: no people placement locations in input'
        for i in range(self.numpeople):
            p = Person(i, self.rate_generator(),
                       self.strategy_generator(),
                       self.location_sampler(av_locs))
            self.people += [p]

        for loc in bottleneck_locs:
            b = Bottleneck(loc)
            self.bottlenecks[loc] = b
        self.fires.update(set(fire_locs))

        self.r, self.c = r+1, c+1

        print(
            '='*79,
            'initialized a {}x{} floor with {} people in {} locations'.format(
                self.r, self.c, len(self.people), len(av_locs)
            ),
            'initialized {} bottleneck(s)'.format(len(self.bottlenecks)),
            'detected {} fire zone(s)'.format(len([loc for loc in self.graph
                                                   if self.graph[loc]['F']])),
            '\ngood luck escaping!', '='*79, 'LOGS', sep='\n'
        )

    def visualize(self, t):
        if self.gui:
            self.plotter.visualize(self.graph, self.people, t)

    def update_bottlenecks(self):
        '''
        handles the bottleneck zones on the grid, where people cannot all pass
        at once. for simplicity, bottlenecks are treated as queues
        '''

        for key in self.bottlenecks:
            #print(key, self.bottlenecks[key])
            personLeaving = self.bottlenecks[key].exitBottleNeck()
            if (personLeaving != None):
                self.sim.sched(self.update_person, personLeaving.id, offset=0)

        if self.numsafe + self.numdead >= self.numpeople:
            return

        if self.maxtime and self.sim.now >= self.maxtime:
            return
        else:
            self.sim.sched(self.update_bottlenecks,
                           offset=self.bottleneck_delay)

    def update_person(self, person_ix):
        '''
        handles scheduling an update for each person, by calling move() on them.
        move will return a location decided by the person, and this method will
        handle the simulus scheduling part to keep it clean
        '''
        if self.maxtime and self.sim.now >= self.maxtime:
            return

        p = self.people[person_ix]
        # if self.graph[p.loc]['F'] or not p.alive:
        #     p.alive = False
        #     self.numdead += 1
        #     if self.verbose:
        #         print('{:>6.2f}\tPerson {:>3} at {} could not make it'.format(
        #             self.sim.now,
        #             p.id, p.loc))
        #     return
        if p.safe:
            self.numsafe += 1
            p.exit_time = self.sim.now
            self.exit_times += [p.exit_time]
            self.avg_exit += p.exit_time
            if self.verbose:
                print('{:>6.2f}\tPerson {:>3} is now SAFE!'.format(self.sim.now,
                                                                   p.id))
            return

        loc = p.loc
        square = self.graph[loc]
        nbrs = [(coords, self.graph[coords]) for coords in square['nbrs']]

        target = p.move(nbrs)
        if not target:
            p.alive = False
            self.numdead += 1
            if self.verbose:
                print('{:>6.2f}\tPerson {:>3} at {} got trapped in fire'.format(
                    self.sim.now,
                    p.id, p.loc))
            return
        square = self.graph[target]
        if square['B']:
            b = self.bottlenecks[target]
            b.enterBottleNeck(p)
        elif square['F']:
            p.alive = False
            self.numdead += 1
            return
        else:
            t = 1/p.rate
            if self.sim.now + t >= (self.maxtime or float('inf')):
                if square['S']:
                    self.nummoving += 1
                else:
                    self.numdead += 1
            else:
                self.sim.sched(self.update_person, person_ix, offset=1/p.rate)

        if (1+person_ix) % int(self.numpeople**.5) == 0:
            self.visualize(t=self.animation_delay/len(self.people)/2)

        # self.sim.show_calendar()

    def simulate(self, maxtime=None, gui=False):
        '''
        sets up initial scheduling and calls the sim.run() method in simulus
        '''
        self.gui = gui
        if self.gui:
            from viz import Plotter
            self.plotter = Plotter()

        # set initial movements of all the people
        for i, p in enumerate(self.people):
            loc = tuple(p.loc)
            square = self.graph[loc]
            nbrs = square['nbrs']
            self.sim.sched(self.update_person, i, offset=1/p.rate)

        self.sim.sched(self.update_bottlenecks, offset=self.bottleneck_delay)

        self.maxtime = maxtime
        self.sim.run()

        self.avg_exit /= max(self.numsafe, 1)

    def stats(self):
        '''
        computes and outputs useful stats about the simulation for nice output
        '''
        print('\n\n', '='*79, sep='')
        print('STATS')

        def printstats(desc, obj):
            print('\t',
                  (desc+' ').ljust(30, '.') + (' '+str(obj)).rjust(30, '.'))

        printstats('total # people', self.numpeople)
        printstats('# people safe', self.numsafe)
        printstats('# people dead', self.numpeople-self.numsafe-self.nummoving)
        printstats('# people gravely injured', self.nummoving)
        print()
        # printstats('total simulation time', '{:.3f}'.format(self.sim.now))
        if self.avg_exit:
            printstats('average time to safe', '{:.3f}'.format(self.avg_exit))
        else:
            printstats('average time to safe', 'NA')
        print()

        # print(self.parser.tostr(self.graph))
        self.visualize(4)

