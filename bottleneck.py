from collections import deque

class Bottleneck():
    loc = None, None
    queue = None
    numInQueue = 0

    # takes a person, and inserts them into the queue of the bottleneck
    def enterBottleNeck(self, person, throughput=1):
        self.queue.append(person)
        self.numInQueue = self.numInQueue + throughput

    # removes a person from the queue
    def exitBottleNeck(self, throughput=1):
        if(len(self.queue) > 0):
            personLeaving = self.queue.pop()
            self.numInQueue = self.numInQueue - throughput
            return personLeaving
        return None

    def __init__(self, loc):
        self.loc = loc
        self.queue = deque()