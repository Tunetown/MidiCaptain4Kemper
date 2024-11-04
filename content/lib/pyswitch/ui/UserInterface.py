from displayio import Group

from .elements.DisplayElement import HierarchicalDisplayElement, DisplayBounds
from .elements.elements import DisplayLabel


# Implements the UI
class UserInterface:

    def __init__(self, display, font_loader):
        self._display = display
        self.font_loader = font_loader

        self._root = HierarchicalDisplayElement(
            bounds = DisplayBounds(0, 0, display.width, display.height),
            name = "Root"
        )
        self._root_initialized = False

        # Splash
        self.splash = Group()
        self._display.tft.rootgroup = self.splash

    # Root element (contains all other elements)
    @property
    def root(self):
        return self._root

    # Show the user interface
    def show(self, appl):
        # Set up the display areas internally (late). This avoids unnecessary 
        # re-creating of splash items (after this, every change to the dimensions
        # of a display label will trigger a performance-costly re-creation of the (Round)Rects)
        if not self._root_initialized:
            self._root.init(self, appl)
            self._root_initialized = True

        # Show the splash on the screen
        self._display.tft.show(self.splash)

    # Creates a label
    def create_label(self, bounds = DisplayBounds(), layout = {}, name = "", id = 0):
        return DisplayLabel(
            bounds = bounds,
            layout = layout,
            name = name,
            id = id if id else name
        )
    
