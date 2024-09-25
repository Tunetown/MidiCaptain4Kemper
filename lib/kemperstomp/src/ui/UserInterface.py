import displayio

from ..hardware.FontLoader import FontLoader
from .elements.base.HierarchicalDisplayElement import HierarchicalDisplayElement
from .DisplayBounds import DisplayBounds


# Implements the UI
class UserInterface:
    def __init__(self, display):
        self.splash = None

        self._display = display
        self._root = HierarchicalDisplayElement(
            bounds = DisplayBounds(0, 0, display.width, display.height),
            name = "Root"
        )
        self._initialized = False

        # Buffered font loader
        self.font_loader = FontLoader()

        # Splash
        self.splash = displayio.Group()
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
        self._root.init(self, appl)

        # Show the splash on the screen
        self._display.tft.show(self.splash)

        self._initialized = True

   