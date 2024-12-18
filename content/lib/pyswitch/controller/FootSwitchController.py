from ..misc import Colors, get_option


# Controller class for a Foot Switch. Each foot switch has three Neopixels.
class FootSwitchController: #ConditionListener

    # config must be a dictionary holding the following attributes:
    # { 
    #     "assignment": {
    #         "model":         Model instance for the switch hardware. Must implement an init() method and a .pushed property.
    #         "pixels":        List of indexes for the Neopixels that belong to this switch, for example (0, 1, 2)
    #     },
    #
    #     "actions": [         Array of actions. Entries must be either Action instances or Conditions with Action
    #                          instance(s) inside (conditions can be deep).
    #         ExampleAction({
    #             ...                  
    #         }),
    #         ...
    #     ],
    # }
    def __init__(self, appl, config):
        self.pixels = get_option(config["assignment"], "pixels", [])
        
        self._switch = config["assignment"]["model"]
        self._switch.init()

        self.id = get_option(config["assignment"], "name", repr(self._switch))

        self._appl = appl
        self._pushed_state = False

        self._colors = [(0, 0, 0) for i in range(len(self.pixels))]
        self._brightnesses = [0 for i in range(len(self.pixels))]        

        self.color = Colors.WHITE
        self.brightness = 0.5

        self.actions = get_option(config, "actions", [])
        self._init_actions()
        
    # Set up action instances
    def _init_actions(self):
        for action in self.actions:
            action.init(self._appl, self)
            
            self._appl.add_updateable(action)
            
            action.update_displays()
        
    # Process the switch: Check if it is currently pushed, set state accordingly
    def process(self):
        # Is the switch currently pushed? If not, return false.
        if not self.pushed:
            if self._pushed_state:
                self._pushed_state = False

                # Process all release actions assigned to the switch 
                for action in self.actions:
                    if not action.enabled:
                        continue

                    action.release()

            return

        # Switch is pushed: Has it been pushed before already? 
        if self._pushed_state:
            return 
        
        # Mark as pushed (prevents redundant messages in the following ticks, when the switch can still be down)
        self._pushed_state = True

        # Process all push actions assigned to the switch     
        for action in self.actions:
            if not action.enabled:
                continue

            action.push()
        
    # Return if the (hardware) switch is currently pushed
    @property
    def pushed(self):
        return self._switch.pushed
                    
    # Colors of the switch (array)
    @property
    def colors(self):
        return self._colors

    # Set switch colors (each of the LEDs individually). Does not take any effect until
    # set_brightness is called!
    @colors.setter
    def colors(self, colors):
        if len(colors) != len(self.pixels):
            raise Exception(repr(len(colors))) #"Invalid amount of colors: " + repr(len(colors)))
        
        if not isinstance(colors, list):
            raise Exception(repr(colors)) #"Invalid type for colors, must be a list: " + repr(colors))
        
        self._colors = colors        

    # Color (this just uses the first one)
    @property
    def color(self):
        if not self.pixels:
            return None
        
        return self._colors[0]

    # Set switch color (all three LEDs equally). Does not take any effect until
    # set_brightness is called!
    @color.setter
    def color(self, color):
        for i in range(len(self.pixels)):
            self._colors[i] = color

    # Returns current brightness (this just uses the first one)
    @property
    def brightness(self):
        if not self.pixels:
            return None
        
        return self._brightnesses[0]

    # Set brightness equally of all LEDs
    @brightness.setter
    def brightness(self, brightness):
        b = []
        for i in range(len(self.pixels)):
            b.append(brightness)
        
        self.brightnesses = b
    
    # Returns current brightnesses of all LEDs
    @property
    def brightnesses(self):
        return self._brightnesses

    # Set brightnesses of all LEDs
    @brightnesses.setter
    def brightnesses(self, brightnesses):
        if not self.pixels:
            return
        
        if len(brightnesses) != len(self.pixels):
            raise Exception() #"Invalid amount of colors: " + repr(len(brightnesses)))
        
        for i in range(len(self.pixels)):
            pixel = self.pixels[i]
            self._appl.led_driver.leds[pixel] = (
                int(self._colors[i][0] * brightnesses[i]),   # R
                int(self._colors[i][1] * brightnesses[i]),   # G
                int(self._colors[i][2] * brightnesses[i])    # B
            )

        self._brightnesses = brightnesses


################################################################################################


## Base class for implementing switch driver classes
#class SwitchDriver:
#    
#    # Initializes the switch. Called once before usage.
#    def init(self):
#        pass
#
#    # Return if the switch is currently pushed (bool).
#    @property
#    def pushed(self):
#        return False
    
