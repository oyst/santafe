from copy import deepcopy
from time import sleep
import sys

class SimWatcher(object):
    def notify_interaction(self):
        pass
    def notify_observation(self):
        pass

class Simulator(object):
    CELL_FOOD = 1
    CELL_EMPTY = 0

    def interaction(func):
        def wrapper(self):
            if self.interactions < self.max_interactions:
                self.interactions += 1
                func(self)
                for watcher in self.watchers:
                    watcher.notify_interaction()
        return wrapper

    def observation(func):
        def wrapper(self):
            res = func(self)
            for watcher in self.watchers:
                watcher.notify_observation()
            return res
        return wrapper

    def __init__(self, max_interactions):
        self.max_interactions = max_interactions
        self.routine = None
        self.start_location = (0, 0)
        self.start_direction = (0, 1)
        self.stored_trail = None
        self._reset()
        self.watchers = []

    def _reset(self):
        self.x, self.y = self.start_location
        self.dir = self.start_direction
        self.interactions = 0
        self.reward = 0
        if self.stored_trail:
            self.trail = deepcopy(self.stored_trail)

    def run(self, routine):
        self._reset()
        while self.interactions < self.max_interactions:
            routine()

    def register_watcher(self, watcher):
        self.watchers.append(watcher)

    def unregister_watcher(self, watcher):
        if watcher in self.watchers:
            self.watchers.remove(watcher)

    def parse_trail(self, trail):
        self.trail = {}
        start_found = False
        for y, row in enumerate(trail):
            for x, cell in enumerate(row):
                if cell == "#":
                    self.trail[x, y] = self.CELL_FOOD
                else:
                    self.trail[x, y] = self.CELL_EMPTY

                if cell in "^>v<":
                    if start_found:
                        raise Exception("Multiple starts were found")
                    start_found = True
                    self.start_location = (x, y)
                    if cell == "^": self.start_direction = (0, -1)
                    if cell == ">": self.start_direction = (1, 0)
                    if cell == "v": self.start_direction = (0, 1)
                    if cell == "<": self.start_direction = (-1, 0)

        self.trail_height  = y
        self.trail_width = x

        if not start_found:
            raise Exception("No starting position found")

        # Backup the trail so that we can modify it and reset
        self.stored_trail = deepcopy(self.trail)

    @interaction
    def turn_left(self):
        self.dir = (-self.dir[1], self.dir[0])

    @interaction
    def turn_right(self):
        self.dir = (self.dir[1], -self.dir[0])

    @interaction
    def move_forward(self):
        self.x, self.y = self.next_location()

        if self.trail[self.x, self.y] == self.CELL_FOOD:
            self.reward += 1
            self.trail[self.x, self.y] = self.CELL_EMPTY

    def next_location(self):
        x, y = self.x, self.y

        x += self.dir[0]
        y += self.dir[1]

        x = max(min(x, self.trail_width - 1), 0)
        y = max(min(y, self.trail_height - 1), 0)

        return (x, y)

    @observation
    def food_ahead(self):
        x, y = self.next_location()
        return self.trail[x, y] == self.CELL_FOOD

    @observation
    def food_around(self):
        found = False
        for d in range(4):
            self.dir = (self.dir[1], -self.dir[0])
            x, y = self.next_location()
            if self.trail[x, y] == self.CELL_FOOD:
                found = True
        return found
