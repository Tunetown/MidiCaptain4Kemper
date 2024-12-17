from micropython import const
from ..misc import DEFAULT_SWITCH_COLOR, Updateable, get_option
#from ...stats import RuntimeStatistics

class Callback(Updateable):
    def __init__(self, mappings = []):
        super().__init__()
        
        self.__initialized = False
        self.__mappings = []

        for m in mappings:
            self.register_mapping(m)

    # Must be used to register all mappings needed by the callback
    def register_mapping(self, mapping):
        if self.__initialized:
            raise Exception() # TODO
        
        self.__mappings.append(mapping)

    # Must be called before usage
    def init(self, appl, listener = None):
        if self.__initialized: 
            return
        
        self.__appl = appl
        self.__listener = listener

        for m in self.__mappings:
            self.__appl.client.register(m, self)

        self.__appl.add_updateable(self)

        self.__initialized = True

    # Reset state
    def reset(self):
        pass                   # pragma: no cover

    #@RuntimeStatistics.measure
    def update(self):
        cl = self.__appl.client

        for m in self.__mappings:
            cl.request(m, self)

    def parameter_changed(self, mapping):
        # Take over value before calling the listener
        for m in self.__mappings:
            if m != mapping:
                continue

            m.value = mapping.value

        if self.__listener:
            self.__listener.parameter_changed(mapping)

    def request_terminated(self, mapping):
        # Clear value before calling the listener
        for m in self.__mappings:
            if m != mapping:
                continue

            m.value = None

        if self.__listener:
            self.__listener.request_terminated(mapping)


###########################################################################################################


class BinaryParameterCallback(Callback):

    # Comparison modes (for the valueEnable value when requesting a value)
    EQUAL = const(0)                 # Enable when exactly the valueEnable value comes in
    
    GREATER = const(10)              # Enable when a value greater than valueEnable comes in
    GREATER_EQUAL = const(20)        # Enable when the valueEnable value comes in, or anything greater

    LESS = const(30)                 # Enable when a value less than valueEnable comes in
    LESS_EQUAL = const(40)           # Enable when the valueEnable value comes in, or anything less

    NO_STATE_CHANGE = const(999)     # Do not receive any values

    def __init__(self, 
                 
                 # A ClientParameterMapping instance. See mappings.py for some predeifined ones.
                 mapping, 

                 # Mapping to be used for disabling the functionality again (only used for sending)
                 mapping_disable = None,

                 # Color to be used
                 color = DEFAULT_SWITCH_COLOR,

                # Color callback (optional, called in update_displays, footprint: get_color())
                 color_callback = None,

                 # Text (optional)
                 text = None,

                 # Text for diabled state (optional)
                 text_disabled = None,

                 # Value to be sent as "enabled". Optional: Default is 1. If mapping.set is a list, this must
                 # also be a list of values for the set messages in the mapping.
                 value_enable = 1,                                       

                 # Value to be sent as "disabled". Optional: Default is 0. If mapping.set is a list, this must
                 # also be a list of values for the set messages in the mapping.
                 # SPECIAL: If you set this (or items of this) to "auto", the "disabled" value will be determined from the 
                 # client's current parameter value when the action state is False (the old value is restored).
                 value_disable = 0,                                      
                 
                 # Optional: The value of incoming messages will be compared against this to determine state
                 # (acc. to the comparison mode). If not set, "valueEnable" is used (first entry if valueEnabled is a list). 
                 reference_value = None,

                 # Mode of comparison when receiving a value. Default is GREATER_EQUAL. 
                 comparison_mode = 20,

                 # Dim factor in range [0..1] for on state (display label) Optional.
                 # If None, the global config value will be used
                 # If "off", the global off config value will be used.
                 display_dim_factor_on = None,

                 # Dim factor in range [0..1] for off state (display label) Optional.
                 # If None, the global config value will be used
                 # If "on", the global on config value will be used.
                 display_dim_factor_off = None,
                 
                 # LED brightness [0..1] for on state (Switch LEDs) Optional.
                 # If None, the global config value will be used
                 # If "off", the global off config value will be used.
                 led_brightness_on = None,

                 # LED brightness [0..1] for off state (Switch LEDs) Optional.
                 # If None, the global config value will be used
                 # If "on", the global on config value will be used.
                 led_brightness_off = None
        ):
        super().__init__(mappings = [mapping])

        self.__mapping = mapping
        self.__mapping_disable = mapping_disable

        self.__value_enable = value_enable
        self.__value_disable = value_disable
        self.__reference_value = reference_value if reference_value != None else ( self.__value_enable if not isinstance(self.__value_enable, list) else self.__value_enable[0] )
        self.__text = text
        self.__text_disabled = text_disabled
        self.__comparison_mode = comparison_mode
        self.__display_dim_factor_on = display_dim_factor_on
        self.__display_dim_factor_off = display_dim_factor_off
        self.__led_brightness_on = led_brightness_on
        self.__led_brightness_off = led_brightness_off
        self.__color = color
        self.__color_callback = color_callback

        self.reset()

        # Auto mode for value_disable
        self.__update_value_disabled = False
        if not isinstance(self.__value_disable, list):
            self.__update_value_disabled = (self.__value_disable == "auto")
        else:
            self.__update_value_disabled = [v == "auto" for v in self.__value_disable]            

    def init(self, appl, listener = None):
        super().init(appl, listener)

        self.__appl = appl

        # Initialize dim factors and brightness settings. 
        if self.__display_dim_factor_on == None:
            self.__display_dim_factor_on = get_option(appl.config, "displayDimFactorOn", 1)
        elif self.__display_dim_factor_on == "off":
            self.__display_dim_factor_on = get_option(appl.config, "displayDimFactorOff", 0.2)
        
        if self.__display_dim_factor_off == None:
            self.__display_dim_factor_off = get_option(appl.config, "displayDimFactorOff", 0.2)
        elif self.__display_dim_factor_off == "on":
            self.__display_dim_factor_off = get_option(appl.config, "displayDimFactorOn", 1)

        if self.__led_brightness_on == None:
            self.__led_brightness_on = get_option(appl.config, "ledBrightnessOn", 0.3)
        elif self.__led_brightness_on == "off":
            self.__led_brightness_on = get_option(appl.config, "ledBrightnessOff", 0.02)

        if self.__led_brightness_off == None:
            self.__led_brightness_off = get_option(appl.config, "ledBrightnessOff", 0.02)
        elif self.__led_brightness_off == "on":
            self.__led_brightness_off = get_option(appl.config, "ledBrightnessOn", 0.3)

    def state_changed_by_user(self, action):
        if action.state:
            set_mapping = self.__mapping
            value = self.__value_enable
        else:
            if self.__mapping_disable:
                set_mapping = self.__mapping_disable
            else:
                set_mapping = self.__mapping

            value = self.__value_disable

        if not isinstance(self.__value_disable, list):
            if value != "auto":
                self.__appl.client.set(set_mapping, value)
        else:
            auto_contained = False
            for v in self.__value_disable:
                if v == "auto":
                    auto_contained = True
                    break
            if not auto_contained:
                self.__appl.client.set(set_mapping, value)

        # Request value
        self.update()

    # Reset state
    def reset(self):
        self._current_display_state = -1
        self._current_value = self       # Just some value which will never occur as a mapping value ;)
        self._current_color = -1

    def update_displays(self, action):
        value = self.__mapping.value

        if value != self._current_value:
            self._current_value = value
            self.evaluate_value(action, value)

        state = action.state
        color = self.__color_callback(action, value) if self.__color_callback else self.__color

        # Set color, if new, or state have been changed
        if color != self._current_color or self._current_display_state != state:
            self._current_color = color
            self._current_display_state = state
        
            self.set_switch_color(action, color)
            self.set_label_color(action, color)
            self.__update_label_text(action)            

    # Evaluate a new value
    def evaluate_value(self, action, value):
        state = False

        if value != None:
            mode = self.__comparison_mode

            if mode == self.EQUAL:
                if value == self.__reference_value:
                    state = True

            elif mode == self.GREATER_EQUAL:
                if value >= self.__reference_value:
                    state = True

            elif mode == self.GREATER:
                if value > self.__reference_value: 
                    state = True

            elif mode == self.LESS_EQUAL:
                if value <= self.__reference_value:
                    state = True

            elif mode == self.LESS:
                if value < self.__reference_value: 
                    state = True        

            elif mode == self.NO_STATE_CHANGE:
                state = action.state

            else:
                raise Exception() #"Invalid comparison mode: " + repr(self.__comparison_mode))        

        action.feedback_state(state)        

        # If enabled, remember the value for later when disabled
        if state == True or not self.__update_value_disabled or value == None:
            return
        
        if not isinstance(self.__value_disable, list):
            self.__value_disable = value
        else:
            vd = self.__value_disable
            for i in range(len(vd)):
                if self.__update_value_disabled[i]:
                    vd[i] = value

    # Update switch brightness
    def set_switch_color(self, action, color):
        # Update switch LED color 
        action.switch_color = color

        if action.state == True and self.__mapping.response:
            # Switched on
            action.switch_brightness = self.__led_brightness_on
        else:
            # Switched off
            action.switch_brightness = self.__led_brightness_off

   # Update label color, if any
    def set_label_color(self, action, color):
        if not action.label:
            return
            
        if action.state == True and self.__mapping.response:
            action.label.back_color = self.dim_color(color, self.__display_dim_factor_on)
        else:
            action.label.back_color = self.dim_color(color, self.__display_dim_factor_off)

    # Update text if set
    def __update_label_text(self, action):
        if not action.label:
            return
            
        if not self.__text:
            return
        
        if action.state == True or not self.__mapping.response:
            action.label.text = self.__text
        else:
            if self.__text_disabled:
                action.label.text = self.__text_disabled
            else:
                action.label.text = self.__text

    # Dims a passed color for display of disabled state
    def dim_color(self, color, factor):
        if isinstance(color[0], tuple):
            # Multi color
            ret = []
            for c in color:
                ret.append((
                    int(c[0] * factor),
                    int(c[1] * factor),
                    int(c[2] * factor)
                ))
            return ret
        else:
            # Single color
            return (
                int(color[0] * factor),
                int(color[1] * factor),
                int(color[2] * factor)
            )
        

###########################################################################################################


# Used for effect enable/disable. Abstract, must implement some methods (see end of class)
class EffectEnableCallback(BinaryParameterCallback):

    # The "None" Type is defined here, all others in derived classes
    CATEGORY_NONE = const(0)

    # Only used on init and reset
    CATEGORY_INITIAL = const(-1)
    
    def __init__(self, mapping_state, mapping_type):
        def color_callback(action, value):
            return self.get_effect_category_color(self.__effect_category)

        super().__init__(
            mapping = mapping_state, 
            color_callback = color_callback
        )

        self.register_mapping(mapping_type)

        self.mapping_fxtype = mapping_type
        
        self.__effect_category = self.CATEGORY_NONE  
        self.__current_category = self.CATEGORY_INITIAL        
        
    def reset(self):
        super().reset()
        
        self.__current_category = self.CATEGORY_INITIAL

    def update_displays(self, action):  
        self.__effect_category = self.get_effect_category(self.mapping_fxtype.value) if self.mapping_fxtype.value != None else self.CATEGORY_NONE
        
        if self.__effect_category == self.CATEGORY_NONE:
            action.feedback_state(False)

        if self.__current_category == self.__effect_category:
            super().update_displays(action)
            return

        self.__current_category = self.__effect_category

        # Effect category text
        if action.label:
            action.label.text = self.get_effect_category_text(self.__effect_category)

        super().update_displays(action)

    # Must return the effect category for a mapping value
    def get_effect_category(self, kpp_effect_type):
        pass                                           # pragma: no cover

    # Must return the color for a category    
    def get_effect_category_color(self, category):
        pass                                           # pragma: no cover

    # Must return the text to show for a category    
    def get_effect_category_text(self, category):
        pass                                           # pragma: no cover
