import curses
from sim import Simulator, SimWatcher
from time import sleep

class CursesRenderer(SimWatcher):
    def __init__(self):
        self.initialised = False

    def init(self, width, height):
        stdscr = curses.initscr()
        curses.echo()
        curses.cbreak()

        self.win = curses.newwin(width + 1, height + 1, 0, 0)
        curses.curs_set(0)
        self.win.border(1)
        self.win.nodelay(1)
        self.height = height
        self.width = width

    def notify_observation(self):
        self._draw()
        sleep(0.1)

    def notify_interaction(self):
        self._draw()
        sleep(0.3)

    def render(self, simulation):
        simulation.register_watcher(self)
        self.sim = simulation
        self.init(self.sim.trail_width, self.sim.trail_height)
        self._draw()

    def _draw(self):
        for x in range(0, self.width):
            for y in range(0, self.height):
                if x == self.sim.x and y == self.sim.y:
                    if self.sim.dir == (0, -1): ch = "^"
                    if self.sim.dir == (1, 0): ch = ">"
                    if self.sim.dir == (0, 1): ch = "v"
                    if self.sim.dir == (-1, 0): ch = "<"
                    self.win.addch(y, x, ch)
                elif self.sim.trail[x, y] == self.sim.CELL_FOOD:
                    self.win.addch(y, x, "#")
                else:
                    self.win.addch(y, x, ".")

        self.win.refresh()

    def close(self):
        curses.curs_set(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
