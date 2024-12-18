from ..misc import Colors, get_option, PeriodCounter
from array import array

# Controller class for a Foot Switch. Each foot switch has three Neopixels.
class FootSwitchController: #ConditionListener

    DEFAULT_HOLD_TIME_MILLIS = 600

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
    #     "actionsHold":        List of actions to perform on holding the switch. Optional.
    #     "holdTimeMillis":     Optional hold time in milliseconds. Default is DEFAULT_HOLD_TIME_MILLIS.
    # }
    def __init__(self, appl, config, period_counter_hold = None):
        self.pixels = get_option(config["assignment"], "pixels", [])
        
        self.__switch = config["assignment"]["model"]
        self.__switch.init()

        #self.id = get_option(config["assignment"], "name", repr(self.__switch))

        self.__appl = appl
        self.__pushed_state = False

        self.__colors = [(0, 0, 0) for i in range(len(self.pixels))]
        self.__brightnesses = array('f', (0 for i in range(len(self.pixels))))

        self.color = Colors.WHITE
        self.brightness = 0.5

        self.__hold_active = False

        self.__actions = get_option(config, "actions", [])
        self.__actions_hold = get_option(config, "actionsHold", [])
        
        # Init actions
        for action in self.__actions + self.__actions_hold:
            action.init(self.__appl, self)
            self.__appl.add_updateable(action)            
            action.update_displays()

        # Hold period counter
        self.__period_hold = period_counter_hold
        if not self.__period_hold:
            hold_time_ms = get_option(config, "holdTimeMillis", self.DEFAULT_HOLD_TIME_MILLIS)
            self.__period_hold = PeriodCounter(hold_time_ms)
        
    # Process the switch: Check if it is currently pushed, set state accordingly
    def process(self):
        # Is the switch currently pushed? If not, return false.
        if not self.pushed:
            if self.__pushed_state:
                self.__pushed_state = False

                # Process all release actions assigned to the switch 
                def release():
                    if self.__actions_hold:    
                        if not self.__hold_active:
                            return
                                                
                        if self.__check_hold():
                            return

                    for action in self.__actions:
                        if not action.enabled:
                            continue

                        if self.__actions_hold:
                            action.push()

                        action.release()

                    self.__hold_active = False
                    
                release()

            return
        else:
            if self.__hold_active and self.__check_hold():
                return

        if self.__pushed_state:
            return 
        
        # Mark as pushed (prevents redundant messages in the following ticks, when the switch can still be down)
        self.__pushed_state = True

        # Process all push actions assigned to the switch     
        if self.__actions_hold:        
            self.__period_hold.reset()
            self.__hold_active = True
            return
        
        for action in self.__actions:
            if not action.enabled:
                continue

            action.push()

    # Checks hold time and triggers hold action if exceeded.
    def __check_hold(self):
        if self.__period_hold.exceeded:
            self.__hold_active = False

            # Hold click
            for action in self.__actions_hold:
                if not action.enabled:
                    continue

                action.push()        
                action.release()

            return True
        
        return False        # Switch is pushed: Has it been pushed before already? 
            
    @property 
    def actions(self):
        return self.__actions + self.__actions_hold

    # Return if the (hardware) switch is currently pushed
    @property
    def pushed(self):
        return self.__switch.pushed
                    
    # Colors of the switch (array)
    @property
    def colors(self):
        return self.__colors

    # Set switch colors (each of the LEDs individually). Does not take any effect until
    # set_brightness is called!
    @colors.setter
    def colors(self, colors):
        if len(colors) != len(self.pixels):
            raise Exception(repr(len(colors))) #"Invalid amount of colors: " + repr(len(colors)))
        
        if not isinstance(colors, list):
            raise Exception(repr(colors)) #"Invalid type for colors, must be a list: " + repr(colors))
        
        self.__colors = colors        

    # Color (this just uses the first one)
    @property
    def color(self):
        if not self.pixels:
            return None
        
        return self.__colors[0]

    # Set switch color (all three LEDs equally). Does not take any effect until
    # set_brightness is called!
    @color.setter
    def color(self, color):
        for i in range(len(self.pixels)):
            self.__colors[i] = color

    # Returns current brightness (this just uses the first one)
    @property
    def brightness(self):
        if not self.pixels:
            return None
        
        return self.__brightnesses[0]

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
        return [b for b in self.__brightnesses]

    # Set brightnesses of all LEDs
    @brightnesses.setter
    def brightnesses(self, brightnesses):
        if not self.pixels:
            return
        
        if len(brightnesses) != len(self.pixels):
            raise Exception() #"Invalid amount of colors: " + repr(len(brightnesses)))
        
        for i in range(len(self.pixels)):
            pixel = self.pixels[i]
            self.__appl.led_driver.leds[pixel] = (
                int(self.__colors[i][0] * brightnesses[i]),   # R
                int(self.__colors[i][1] * brightnesses[i]),   # G
                int(self.__colors[i][2] * brightnesses[i])    # B
            )

        self.__brightnesses = array('f', brightnesses)


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
    
