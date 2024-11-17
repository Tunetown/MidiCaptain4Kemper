import math
from ...misc import get_option, Updateable, DEFAULT_SWITCH_COLOR, DEFAULT_LABEL_COLOR #, do_print


# Base class for actions. All functionality is encapsulated in a class for each, 
# inheriting from Action.
class Action(Updateable):
    
    _next_id = 0   # Global counted action ids (internal, just used for debugging!)

    # config: {
    #      "display": {
    #          "area":             ID of the display area. See displays defintion in config.
    #          "index":            Position inside the display area (optional for split container display areas). If omitted, always the first 
    #                              place is used which takes up the whole area space. 
    #          "layout":           Layout definition for the action label (mandatory)
    #      },
    #
    #      "enabled": True,        Optional bool parameter to disable/enable the action. Mostly used internally only. Defaults to True 
    #                              when not specified.
    # 
    #      "color":                Color for switch and display (optional, default: white). Can be either one color or a tuple of colors
    #                              with one color for each LED segment of the switch (if more actions share the LEDs, only the first
    #                              color is used).
    #
    #      "id":                   Optional ID for debugging. If not set, an automatic ID is generated.
    # }
    def __init__(self, config = {}):
        self.uses_switch_leds = False             # Must be set True explicitly by child classes in __init__() if they use the switch LEDs
        self._initialized = False

        self._display_id = None
        self._display_index = None
        self._display_layout = None

        self.id = get_option(config, "id", None)
        self.color = get_option(config, "color", DEFAULT_SWITCH_COLOR)
        self._enabled = get_option(config, "enabled", True)
        self._label_color = get_option(config, "color", None)

        display = get_option(config, "display", None)
        if display:
            self._display_id = get_option(display, "id", None)
            self._display_index = get_option(display, "index", None)
            self._display_layout = get_option(display, "layout", None)

    #def __repr__(self):
    #    return self.__class__.__name__ + " " + repr(self.id)

    # Must be called before usage
    def init(self, appl, switch):
        self.appl = appl
        self.switch = switch

        #self._init_id()

        self.label = self._get_display_label()   # DisplayLabel instance the action is connected to (or None).

        self._initialized = True

    # Sets up the debugging ID (either from config or a generated one)
    #def _init_id(self):
    #    if not self.id:
    #        self.id = self.switch.id + " | " + self.__class__.__name__ + " (" + repr(Action._next_id) + ")"
    #        
    #        Action._next_id = Action._next_id + 1

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if self._enabled == value:
            return 
        
        self._enabled = value

        self.force_update()
        self.update_displays()

    # Color of the switch segment(s) for the action (Difficult to do with multicolor, 
    # but this property is just needed to have a setter so this is not callable)
    @property
    def switch_color(self):  # pragma: no cover
        raise Exception() #"Getter not implemented (yet)")

    # color can also be a tuple!
    @switch_color.setter
    def switch_color(self, color):
        segments = self._get_led_segments()
        if len(segments) == 0:
            return
        
        tmp = self.switch.colors

        if isinstance(color[0], tuple):
            if len(segments) == len(color):
                # Fills all LEDs: Just pass colors
                for i in range(len(segments)):
                    tmp[segments[i]] = color[i]
            else:
                # Only fills some LEDs: Use a middle color
                for segment in segments:
                    tmp[segment] = color[math.floor(len(color) / 2)]
        else:
            # Single color: Fill all segments
            for segment in segments:
                tmp[segment] = color

        self.switch.colors = tmp

    # Brightness of the switch segment(s) for the action
    @property
    def switch_brightness(self):
        segments = self._get_led_segments()
        if len(segments) > 0:
            return self.switch.brightnesses[segments[0]]  # Return the first segment as they are all equal
        return None

    @switch_brightness.setter
    def switch_brightness(self, brightness):
        segments = self._get_led_segments()
        if len(segments) == 0:
            return
                
        tmp = self.switch.brightnesses
        for segment in segments:
            tmp[segment] = brightness

        self.switch.brightnesses = tmp

    # Called regularly every update interval to update status of effects etc.
    def update(self):
        if not self.enabled:
            return
                
        self.do_update()

    # Perform updates (to be redefined)
    def do_update(self):
        pass                                      # pragma: no cover

    # Called when the switch is pushed down
    def push(self):
        pass                                      # pragma: no cover

    # Called when the switch is released
    def release(self):
        pass                                      # pragma: no cover

    # Called to update the displays (LEDs and label)
    def update_displays(self):
        pass                                      # pragma: no cover

    # Reset the action
    def reset(self):
        pass                                      # pragma: no cover

    # Must reset all action states so the instance is being updated
    def force_update(self):
        pass                                      # pragma: no cover

    # Must reset the displays
    def reset_display(self):
        pass                                      # pragma: no cover

    # Get the assigned label reference from the UI (or None)
    def _get_display_label(self):
        if not self._display_id:
            return None
        
        label = self.appl.ui.search(self._display_id, self._display_index)
        if label:
            return label
        
        # Not yet existent: Get container
        container = self.appl.ui.search(self._display_id)        

        if not container:
            raise Exception("Display " + repr(self._display_id) + " not found")
        
        if self._display_index == None:
            return container

        layout = self._display_layout
        
        # Set the color as the number of items cannot be changed later!
        layout["backColor"] = self._label_color if self._label_color else ( layout["backColor"] if "backColor" in layout else DEFAULT_LABEL_COLOR )

        label = self.appl.ui.create_label(
            layout = layout,
            name = self.id
        )

        container.set(label, self._display_index)

        self._display_id = None
        self._display_index = None
        self._display_layout = None
        
        return label

    # Returns the switch LED segments to use
    def _get_led_segments(self):
        if not self.switch.pixels or not self.uses_switch_leds or not self.enabled:
            return []
        
        actions_using_leds = self._get_actions_using_leds()

        ret = []

        index = self._get_index_among_led_actions(actions_using_leds)
        num_pixels = len(self.switch.pixels)

        if len(actions_using_leds) == 1:
            for i in range(num_pixels):
                ret.append(i)                
        
        elif len(actions_using_leds) < num_pixels:
            pixels_for_first = num_pixels - len(actions_using_leds) + 1

            if index == 0:
                ret = [i for i in range(0, pixels_for_first)]
            else:
                ret = [pixels_for_first + index - 1]

        elif index < num_pixels:
            ret = [index]

        return ret

    # Returns the index of this action inside the LED-using actions of the switch.
    def _get_index_among_led_actions(self, actions_using_leds):
        for i in range(len(actions_using_leds)):
            if actions_using_leds[i] == self:
                return i
        
        raise Exception() #"Action " + repr(self.id) + " not found in LED-using actions of switch " + repr(self.switch.id))

    # Returns a list of the actions of the switch which are both enabled and use LEDs.
    def _get_actions_using_leds(self):
        ret = [] 

        for a in self.switch.actions:
            sub = a.get_all_actions()
            ret = ret + [s for s in sub if s.uses_switch_leds and s.enabled]

        return ret

    # Must return a list containing self and all possible sub actions
    def get_all_actions(self):
        return [self]

    # Print to the debug console
    #def print(self, msg):    # pragma: no cover
    #    enabled_text = "on" if self.enabled else "off"

    #    do_print(self.id + " (" + enabled_text + "): " + msg)

