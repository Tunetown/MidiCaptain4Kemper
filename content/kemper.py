from math import floor
from micropython import const

from adafruit_midi.control_change import ControlChange
from adafruit_midi.system_exclusive import SystemExclusive

from pyswitch.misc import Colors, PeriodCounter, DEFAULT_SWITCH_COLOR, DEFAULT_LABEL_COLOR, formatted_timestamp, do_print
from pyswitch.controller.actions.actions import ParameterAction, EffectEnableAction, ResetDisplaysAction, PushButtonAction
from pyswitch.controller.Client import ClientParameterMapping


####################################################################################################################

# Definitions of devices
_NRPN_PRODUCT_TYPE_PROFILER = const(0x00)                     # Kemper Profiler
_NRPN_PRODUCT_TYPE_PROFILER_PLAYER = const(0x02)              # Kemper Profiler Player

# This defines which type of device to control
_NRPN_PRODUCT_TYPE = _NRPN_PRODUCT_TYPE_PROFILER_PLAYER

####################################################################################################################

# ControlChange Addresses
_CC_TUNER_MODE = const(31)
_CC_BANK_INCREASE = const(48)
_CC_BANK_DECREASE = const(49)
_CC_RIG_SELECT = const(50)       # This selects slot 1 of the current bank. The slots 2-5 can be addressed by adding (n-1) to the value.
_CC_BANK_PRESELECT = const(47)
_CC_TAP_TEMPO = const(30)
_CC_ROTARY_SPEED = const(33)     # 1 = Fast, 0 = Slow

_CC_EFFECT_BUTTON_I = const(75)  # II to IV are consecutive from this: 76, 77, 78

_CC_VALUE_BANK_CHANGE = const(0)

# Basic values for all NRPN messages
_NRPN_MANUFACTURER_ID = [0x00, 0x20, 0x33]       # Kemper manufacturer ID
_NRPN_DEVICE_ID_OMNI = const(0x7f)               # Omni (all devices, only supported mode)
_NRPN_INSTANCE = const(0x00)                     # Instance ID for NRPN. The profiler only supports instance 0.

# NRPN Adress pages
_NRPN_ADDRESS_PAGE_STRINGS = const(0x00)
_NRPN_ADDRESS_PAGE_RIG_PARAMETERS = const(0x04)
_NRPN_ADDRESS_PAGE_FREEZE = const(0x7d)
_NRPN_ADDRESS_PAGE_AMP = const(0x0a)
_NRPN_ADDRESS_PAGE_CABINET = const(0x0c)

# NRPN Function codes
_NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER = const(0x41)
_NRPN_FUNCTION_REQUEST_STRING_PARAMETER = const(0x43)
_NRPN_FUNCTION_REQUEST_EXT_STRING_PARAMETER = const(0x47)

_NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER = const(0x01)
_NRPN_FUNCTION_RESPONSE_STRING_PARAMETER = const(0x03)

_NRPN_FUNCTION_SET_SINGLE_PARAMETER = const(0x01)

# NRPN parameters for effect slots
_NRPN_EFFECT_PARAMETER_ADDRESS_TYPE = const(0x00) 
_NRPN_EFFECT_PARAMETER_ADDRESS_STATE = const(0x03)
_NRPN_EFFECT_PARAMETER_ADDRESS_ROTARY_SPEED = const(0x1e)
# ... add further parameters here

# Rig parameters (page 0x04)
_NRPN_RIG_PARAMETER_VOLUME = const(0x01)
# ... add further parameters here

# Amp parameters (page 0x0a)
_NRPN_AMP_PARAMETER_STATE = const(0x02)

# Cab parameters (page 0x0c)
_NRPN_CABINET_PARAMETER_STATE = const(0x02)

# NRPN String parameters
_NRPN_STRING_PARAMETER_ID_RIG_NAME = const(0x01)
_NRPN_STRING_PARAMETER_ID_RIG_DATE = const(0x03)
_NRPN_STRING_PARAMETER_ID_AMP_NAME = const(0x10)
_NRPN_STRING_PARAMETER_ID_CABINET_NAME = const(0x20)

# Generally used NRPN values
_NRPN_PARAMETER_OFF = const(0)
_NRPN_PARAMETER_ON = const(1)


####################################################################################################################


# Kemper Effect slot IDs, MIDI addresses and display properties
class KemperEffectSlot:
    
    # IDs for the available effect slots
    EFFECT_SLOT_ID_A = const(0)
    EFFECT_SLOT_ID_B = const(1)
    EFFECT_SLOT_ID_C = const(2)
    EFFECT_SLOT_ID_D = const(3)
    
    EFFECT_SLOT_ID_X = const(4)
    EFFECT_SLOT_ID_MOD = const(5)
    EFFECT_SLOT_ID_DLY = const(6)
    EFFECT_SLOT_ID_REV = const(7)

    # CC Address for Effect Slot enable/disable. Order has to match the one defined above!
    CC_EFFECT_SLOT_ENABLE = (
        const(17),    # Slot A
        const(18),    # Slot B
        const(19),    # Slot C
        const(20),    # Slot D

        const(22),    # Slot X
        const(24),    # Slot MOD        
        const(27),    # Slot DLY (with Spillover)        
        const(29)     # Slot REV (with Spillover)
    )

    # Slot address pages. Order has to match the one defined above!
    NRPN_SLOT_ADDRESS_PAGE = (
        const(0x32),   # Slot A
        const(0x33),   # Slot B
        const(0x34),   # Slot C
        const(0x35),   # Slot D

        const(0x38),   # Slot X
        const(0x3a),   # Slot MOD
        const(0x3c),   # Slot DLY
        const(0x3d)    # Slot REV
    )    

    # Freeze parameter addresses on page 0x7d (Looper and Delay Freeze) for all slots. 
    # Order has to match the one defined above!
    NRPN_FREEZE_SLOT_PARAMETER_ADDRESSES = [
        const(0x6b),   # Slot A
        const(0x6c),   # Slot B
        const(0x6d),   # Slot C
        const(0x6e),   # Slot D

        const(0x6f),   # Slot X
        const(0x71),   # Slot MOD
        const(0x72),   # Slot DLY
        const(0x73)    # Slot REV
    ]    

     # Slot names for display. Order has to match the one defined above!
    EFFECT_SLOT_NAMES = [
        "A",
        "B",
        "C",
        "D",

        "X",
        "MOD",
        "DLY",
        "REV"
    ]

    def __init__(self, slot_id):
        self._slot_id = slot_id

    # Must return the lot name
    def get_name(self):
        return KemperEffectSlot.EFFECT_SLOT_NAMES[self._slot_id]
    

####################################################################################################################

# All defined actions here have one parameter in common: A display definition (see definitions.py)
# which assigns a display label to the action (optional: If omitted, no visual feedback is given 
# on the display).
class KemperActionDefinitions: 

    ## Effect slots ########################################################################################################

    # Switch an effect slot on / off
    @staticmethod
    def EFFECT_STATE(slot_id, display = None, mode = PushButtonAction.HOLD_MOMENTARY, id = False, use_leds = True):
        return EffectEnableAction({
            "mapping": KemperMappings.EFFECT_STATE(slot_id),
            "mappingType": KemperMappings.EFFECT_TYPE(slot_id),
            "categories": KemperEffectCategories(),
            "slotInfo": KemperEffectSlot(slot_id),
            "mode": mode,
            "display": display,
            "id": id,
            "useSwitchLeds": use_leds
        })

    # Rotary speed (fast/slow)
    @staticmethod
    def ROTARY_SPEED(slot_id, display = None, color = Colors.DARK_BLUE, id = False, use_leds = True):
        return ParameterAction({
            "mapping": KemperMappings.ROTARY_SPEED(slot_id),
            "display": display,
            "text": "Fast",
            "color": color,
            "id": id,
            "useSwitchLeds": use_leds
        })

    ## Special functions ####################################################################################################

    # Switch tuner mode on / off
    @staticmethod
    def TUNER_MODE(display = None, color = DEFAULT_SWITCH_COLOR, id = False, use_leds = True):
        return ParameterAction({
            "mapping": KemperMappings.TUNER_MODE_STATE,
            "valueEnabled": 1,
            "valueDisabled": 3,
            "setValueEnabled": 1,
            "setValueDisabled": 0,
            "comparisonMode": ParameterAction.EQUAL,
            "display": display,
            "text": "Tuner",
            "color": Colors.WHITE,
            "color": color,
            "id": id,
            "useSwitchLeds": use_leds
        })

    # Tap tempo
    @staticmethod
    def TAP_TEMPO(display = None, color = Colors.DARK_GREEN, id = False, use_leds = True):
        return ParameterAction({
            "mapping": KemperMappings.TAP_TEMPO,
            "display": display,
            "text": "Tap",
            "color": color,
            "mode": PushButtonAction.MOMENTARY,
            "id": id,
            "useSwitchLeds": use_leds
        })

    # Effect Button I-IIII (set only). num must be a number (1 to 4).
    @staticmethod
    def EFFECT_BUTTON(num, text = None, display = None, color = Colors.LIGHT_GREEN, id = False, use_leds = True):
        if not text:
            if num == 1:
                text = "FX I"
            elif num == 2:
                text = "FX II"
            elif num == 3:
                text = "FX III"
            elif num == 4:
                text = "FX IIII"

        return ParameterAction({
            "mapping": KemperMappings.EFFECT_BUTTON(num),
            "display": display,
            "text": text,
            "color": color,
            "id": id,
            "useSwitchLeds": use_leds,
            "ledBrightness": {
                "on": ParameterAction.DEFAULT_LED_BRIGHTNESS_OFF,               # Set equal brightness (we do not need status display here)
                "off": ParameterAction.DEFAULT_LED_BRIGHTNESS_OFF
            },
            "displayDimFactor": {
                "on": ParameterAction.DEFAULT_SLOT_DIM_FACTOR_OFF,              # Set equal dim factor (we do not need status display here)
                "off": ParameterAction.DEFAULT_SLOT_DIM_FACTOR_OFF
            }
        })

    ## Rig specific ##########################################################################################################

    # Volume boost function, based on setting rig volume to a certain boost value. To 
    # make sense, all rig volumes have to be zero in your rigs! You can then set the
    # boost rig volume by passing a value in range [0..1] (corresponding to the range of the
    # rig volume paramneter: 0.5 is 0dB, 0.75 is +6dB, 1.0 is +12dB)
    @staticmethod
    def RIG_VOLUME_BOOST(boost_volume, display = None, mode = PushButtonAction.HOLD_MOMENTARY, color = Colors.PINK, id = False, use_leds = True):
        return ParameterAction({
            "mode": mode,
            "mapping": KemperMappings.RIG_VOLUME,
            "valueEnabled": KemperMidiValueProvider.NRPN_VALUE(boost_volume),
            "valueDisabled": KemperMidiValueProvider.NRPN_VALUE(0.5),           # 0dB
            "display": display,
            "text": "RigBoost",
            "color": color,
            "id": id,
            "useSwitchLeds": use_leds
        })

    # Used to reset the screen areas which show rig info details directly after rig changes (if you dont use this, 
    # you get no visual feedback on the device that a new rig is coming up)
    @staticmethod
    def RESET_RIG_INFO_DISPLAYS(id = False):
        return ResetDisplaysAction({
            "resetSwitches": True,
            "ignoreOwnSwitch": True,
            "resetDisplayAreas": True,
            "id": id
        })

    ## Amp ########################################################################################################################

    # Amp on/off
    @staticmethod
    def AMP_STATE(display = None, mode = PushButtonAction.HOLD_MOMENTARY, color = DEFAULT_SWITCH_COLOR, id = False, use_leds = True):
        return ParameterAction({
            "mapping": KemperMappings.AMP_STATE,
            "mode": mode,
            "display": display,
            "text": "Amp",
            "color": color,
            "id": id,
            "useSwitchLeds": use_leds
        })

    ## Cab ########################################################################################################################

    # Amp on/off
    @staticmethod
    def CABINET_STATE(display = None, mode = PushButtonAction.HOLD_MOMENTARY, color = DEFAULT_SWITCH_COLOR, id = False, use_leds = True):
        return ParameterAction({
            "mapping": KemperMappings.CABINET_STATE,
            "mode": mode,
            "display": display,
            "text": "Cab",
            "color": color,
            "id": id,
            "useSwitchLeds": use_leds
        })

    ## Change Rig/Bank ############################################################################################################

    # Next bank (keeps rig index)
    @staticmethod
    def BANK_UP(display = None, color = Colors.WHITE, id = False, use_leds = True):
        return ParameterAction({
            "mapping": KemperMappings.NEXT_BANK,
            "mode": PushButtonAction.ONE_SHOT,
            "valueEnabled": _CC_VALUE_BANK_CHANGE,
            "display": display,
            "text": "Bank up",
            "color": color,
            "id": id,
            "useSwitchLeds": use_leds
        })
    
    # Previous bank (keeps rig index)
    @staticmethod
    def BANK_DOWN(display = None, color = Colors.WHITE, id = False, use_leds = True):
        return ParameterAction({
            "mapping": KemperMappings.PREVIOUS_BANK,
            "mode": PushButtonAction.ONE_SHOT,
            "valueEnabled": _CC_VALUE_BANK_CHANGE,
            "display": display,
            "text": "Bank dn",
            "color": color,
            "id": id,
            "useSwitchLeds": use_leds
        })
    
    # Selects a specific rig, or toggles between two rigs (if rig_off is also provided) in
    # the current bank. Rigs are indexed starting from one, range: [1..5].
    # Optionally, banks can be switched too in the same logic using bank and bank_off.
    @staticmethod
    def RIG_SELECT(rig, rig_off = None, bank = None, bank_off = None, display = None, color = Colors.YELLOW, id = False, use_leds = True):
        # Texts always show the rig to be selected when the switch is pushed the next time
        text_rig_off = str(rig)
        text_rig_on = text_rig_off

        mapping_rig_select = KemperMappings.RIG_SELECT(rig - 1)

        # Mappings and values: Start with a configuration for rig_off == None and bank(_off) = None.
        mapping = [
            ClientParameterMapping(),           # Dummy to be replaced by bank select if specified
            mapping_rig_select
        ]
        mapping_disable = [
            ClientParameterMapping(),           # Dummy to be replaced by bank select if specified
            mapping_rig_select
        ]
        value_enabled = [
            0,                                  # Dummy to be replaced by bank select if specified
            _NRPN_PARAMETER_ON
        ]
        value_disabled = [
            0,                                  # Dummy to be replaced by bank select if specified
            _NRPN_PARAMETER_ON
        ]

        # Bank for main rig
        if bank != None:
            mapping[0] = KemperMappings.BANK_PRESELECT
            if rig_off == None:
                mapping_disable[0] = KemperMappings.BANK_PRESELECT
            
            value_enabled[0] = bank - 1
            value_disabled[0] = bank - 1
            
            text_rig_off = str(bank) + "-" + text_rig_off
            if rig_off == None:
                text_rig_on = text_rig_off

        # Alternate rig (the rig selected when the switch state is False)
        if rig_off != None:
            # Use a different mapping for disabling
            mapping_disable[1] = KemperMappings.RIG_SELECT(rig_off - 1)
            text_rig_on = str(rig_off)

        # Bank for alternate rig
        if bank_off != None:
            if rig_off == None:
                raise Exception("RIG_SELECT: If bank_off is set, you must also provide rig_off.")
            
            mapping_disable[0] = KemperMappings.BANK_PRESELECT
            value_disabled[0] = bank_off - 1
            
            text_rig_on = str(bank_off) + "-" + text_rig_on

        # Finally we can create the action definition ;)
        return ParameterAction({
            "mapping": mapping,
            "mappingDisable": mapping_disable,
            "valueEnabled": value_enabled,
            "valueDisabled": value_disabled,
            "display": display,
            "text": "Rig " + text_rig_on,
            "textDisabled": "Rig " + text_rig_off,
            "color": color,
            "ledBrightness": {
                "on": ParameterAction.DEFAULT_LED_BRIGHTNESS_OFF,               # Set equal brightness (we do not need status display here)
                "off": ParameterAction.DEFAULT_LED_BRIGHTNESS_OFF
            },
            "displayDimFactor": {
                "on": ParameterAction.DEFAULT_SLOT_DIM_FACTOR_OFF,              # Set equal dim factor (we do not need status display here)
                "off": ParameterAction.DEFAULT_SLOT_DIM_FACTOR_OFF
            },
            "mode": PushButtonAction.LATCH,
            "id": id,
            "useSwitchLeds": use_leds
        })


####################################################################################################################


# Provides mapping of the kemper internal effect types to effect categories
class KemperEffectCategories: #(EffectCategoryProvider):

    # Effect types enum (used internally, also for indexing colors, so be sure these are always a row from 0 to n)
    CATEGORY_NONE = const(0)
    CATEGORY_WAH = const(1)
    CATEGORY_DISTORTION = const(2)
    CATEGORY_COMPRESSOR = const(3)
    CATEGORY_NOISE_GATE = const(4)
    CATEGORY_SPACE = const(5)
    CATEGORY_CHORUS = const(6)
    CATEGORY_PHASER_FLANGER = const(7)
    CATEGORY_EQUALIZER = const(8)
    CATEGORY_BOOSTER = const(9)
    CATEGORY_LOOPER = const(10)
    CATEGORY_PITCH = const(11)
    CATEGORY_DUAL = const(12)
    CATEGORY_DELAY = const(13)
    CATEGORY_REVERB = const(14)

    # Effect colors. The order must match the enums for the effect types defined above!
    CATEGORY_COLORS = (
        DEFAULT_LABEL_COLOR,                            # None
        Colors.ORANGE,                                  # Wah
        Colors.RED,                                     # Distortion
        Colors.BLUE,                                    # Comp
        Colors.BLUE,                                    # Gate
        Colors.GREEN,                                   # Space
        Colors.BLUE,                                    # Chorus
        Colors.PURPLE,                                  # Phaser/Flanger
        Colors.YELLOW,                                  # EQ
        Colors.RED,                                     # Booster
        Colors.PURPLE,                                  # Looper
        Colors.WHITE,                                   # Pitch
        Colors.GREEN,                                   # Dual
        Colors.GREEN,                                   # Delay
        Colors.GREEN,                                   # Reverb
    )

    # Effect type display names. The order must match the enums for the effect types defined above!
    CATEGORY_NAMES = (
        "-",
        "Wah",
        "Dist",
        "Comp",
        "Gate",
        "Space",
        "Chorus",
        "Phaser",
        "EQ",
        "Boost",
        "Looper",
        "Pitch",
        "Dual",
        "Delay",
        "Reverb"
    )

    # Must return the effect category for a mapping value
    def get_effect_category(self, kpp_effect_type):
        # NOTE: The ranges are defined by Kemper with a lot of unused numbers, so the borders between types
        # could need to be adjusted with future Kemper firmware updates!
        if (kpp_effect_type == 0):
            return KemperEffectCategories.CATEGORY_NONE
        elif (0 < kpp_effect_type and kpp_effect_type <= 14):
            return KemperEffectCategories.CATEGORY_WAH
        elif (14 < kpp_effect_type and kpp_effect_type <= 45):
            return KemperEffectCategories.CATEGORY_DISTORTION
        elif (45 < kpp_effect_type and kpp_effect_type <= 55):
            return KemperEffectCategories.CATEGORY_COMPRESSOR
        elif (55 < kpp_effect_type and kpp_effect_type <= 60):
            return KemperEffectCategories.CATEGORY_NOISE_GATE       
        elif (60 < kpp_effect_type and kpp_effect_type <= 64):
            return KemperEffectCategories.CATEGORY_SPACE            
        elif (64 < kpp_effect_type and kpp_effect_type <= 80):
            return KemperEffectCategories.CATEGORY_CHORUS
        elif (80 < kpp_effect_type and kpp_effect_type <= 95):
            return KemperEffectCategories.CATEGORY_PHASER_FLANGER
        elif (95 < kpp_effect_type and kpp_effect_type <= 110):
            return KemperEffectCategories.CATEGORY_EQUALIZER
        elif (110 < kpp_effect_type and kpp_effect_type <= 120):
            return KemperEffectCategories.CATEGORY_BOOSTER
        elif (120 < kpp_effect_type and kpp_effect_type <= 125):
            return KemperEffectCategories.CATEGORY_LOOPER
        elif (125 < kpp_effect_type and kpp_effect_type <= 135):
            return KemperEffectCategories.CATEGORY_PITCH
        elif (135 < kpp_effect_type and kpp_effect_type <= 143):
            return KemperEffectCategories.CATEGORY_DUAL
        elif (143 < kpp_effect_type and kpp_effect_type <= 170):
            return KemperEffectCategories.CATEGORY_DELAY
        else:
            return KemperEffectCategories.CATEGORY_REVERB
    
    # Must return the effect color for a mapping value
    def get_effect_category_color(self, kpp_effect_type):
        return KemperEffectCategories.CATEGORY_COLORS[kpp_effect_type]
    
    # Must return the effect name for a mapping value
    def get_effect_category_name(self, kpp_effect_type):
        return KemperEffectCategories.CATEGORY_NAMES[kpp_effect_type]
    
    # Must return the value interpreted as "not assigned"
    def get_category_not_assigned(self):
        return KemperEffectCategories.CATEGORY_NONE


####################################################################################################################


# Kemper specific SysEx message with defaults which are valid most of the time
class KemperNRPNMessage(SystemExclusive):

    def __init__(
            self, 
            function_code,
            address_page,
            address_number,
            manufacturer_id = _NRPN_MANUFACTURER_ID, 
            product_type = _NRPN_PRODUCT_TYPE,
            device_id = _NRPN_DEVICE_ID_OMNI
        ):

        # Adafruit SystemExclusive
        super().__init__(
            manufacturer_id,                 # [0x00, 0x20, 0x33]
            [
                product_type,                # 0x02 (Player), 0x00 (Profiler)
                device_id,                   # 0x7f (omni) or manually set via parameter
                function_code,               # Selects the function, for example 0x41 for requesting a single parameter
                _NRPN_INSTANCE,               # 0x00
                address_page,                # Controller MSB (address page)
                address_number               # Controller LSB (address number of parameter)
            ]
        )
        
# Kemper specific SysEx message for extended parameters 
class KemperNRPNExtendedMessage(SystemExclusive):
    
    def __init__(
            self, 
            function_code,
            controller,     # Must be a list
            manufacturer_id = _NRPN_MANUFACTURER_ID, 
            product_type = _NRPN_PRODUCT_TYPE,
            device_id = _NRPN_DEVICE_ID_OMNI
        ):

        # Adafruit SystemExclusive
        super().__init__(
            manufacturer_id,                 # [0x00, 0x20, 0x33]
            [
                product_type,                # 0x02 (Player), 0x00 (Profiler)
                device_id,                   # 0x7f (omni) or manually set via parameter
                function_code,               # Selects the function, for example 0x41 for requesting a single parameter
                _NRPN_INSTANCE                # 0x00                
            ] + controller
        )

####################################################################################################################


# Implements setting values and parsing request responses
class KemperMidiValueProvider: #(ClientValueProvider):

    # Parameter types (used internally in mappings)
    PARAMETER_TYPE_NUMERIC = const(0)   # Default, also used for on/off
    PARAMETER_TYPE_STRING = const(1)

    # Helper to convert values in range [0..1] to the NRPN value range of [0..16383]
    @staticmethod
    def NRPN_VALUE(value):
        return int(16383 * value)

    # Must parse the incoming MIDI message and set it on the passed mapping.
    # If the response template does not match, must return False.
    # Must return True to notify the listeners of a value change.
    def parse(self, mapping, midi_message):
        # Compare manufacturer IDs
        if midi_message.manufacturer_id != mapping.response.manufacturer_id:
            return False
        
        # Check if the message belongs to the mapping. The following have to match:
        #   2: function code, 
        #   3: instance ID, 
        #   4: address page, 
        #   5: address nunber
        #
        # The first two values are ignored (the Kemper MIDI specification implies this would contain the product type
        # and device ID as for the request, however the device just sends two zeroes)
        if midi_message.data[2:6] != mapping.response.data[2:6]:
            return False
        
        # The values starting from index 6 are the value of the response.
        if mapping.type == self.PARAMETER_TYPE_STRING:
            # Take as string
            mapping.value = ''.join(chr(int(c)) for c in list(midi_message.data[6:-1]))
        else:
            # Decode 14-bit value to int
            mapping.value = midi_message.data[-2] * 128 + midi_message.data[-1]

        return True
    
    # Must set the passed value on the SET message of the mapping.
    def set_value(self, mapping, value):
        if isinstance(mapping.set, ControlChange):
            # Set value directly (CC takes int values)
            mapping.set.value = value

        elif isinstance(mapping.set, SystemExclusive):            
            # Fill up message to appropriate length for the specification
            data = list(mapping.set.data)
            while len(data) < 8:
                data.append(0)
            
            # Set value as 14 bit
            data[6] = int(floor(value / 128))
            data[7] = int(value % 128)

            mapping.set.data = bytes(data)
        

####################################################################################################################


# Defines some useful MIDI mappings
class KemperMappings:

    # Effect slot enable/disable
    @staticmethod
    def EFFECT_STATE(slot_id):
        return ClientParameterMapping(
            name = "Effect Status " + str(slot_id),
            set = ControlChange(
                KemperEffectSlot.CC_EFFECT_SLOT_ENABLE[slot_id], 
                0    # Dummy value, will be overridden
            ),
            request = KemperNRPNMessage(               
                _NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                KemperEffectSlot.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                _NRPN_EFFECT_PARAMETER_ADDRESS_STATE
            ),
            response = KemperNRPNMessage(
                _NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
                KemperEffectSlot.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                _NRPN_EFFECT_PARAMETER_ADDRESS_STATE
            )
        )
    
    # Effect slot type (request only)
    @staticmethod
    def EFFECT_TYPE(slot_id):
        return ClientParameterMapping(
            name = "Effect Type " + str(slot_id),
            request = KemperNRPNMessage(               
                _NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                KemperEffectSlot.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                _NRPN_EFFECT_PARAMETER_ADDRESS_TYPE
            ),
            response = KemperNRPNMessage(               
                _NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER, 
                KemperEffectSlot.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                _NRPN_EFFECT_PARAMETER_ADDRESS_TYPE
            )
        )

   # Rotary speed (fast/slow)
    @staticmethod
    def ROTARY_SPEED(slot_id):
        return ClientParameterMapping(
            name = "Rotary Speed " + str(slot_id),
            set = KemperNRPNMessage(
                _NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
                KemperEffectSlot.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                _NRPN_EFFECT_PARAMETER_ADDRESS_ROTARY_SPEED
            ),
            request = KemperNRPNMessage(               
                _NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                KemperEffectSlot.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                _NRPN_EFFECT_PARAMETER_ADDRESS_ROTARY_SPEED
            ),
            response = KemperNRPNMessage(
                _NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
                KemperEffectSlot.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                _NRPN_EFFECT_PARAMETER_ADDRESS_ROTARY_SPEED
            )
        )

    # Freeze for slot
    @staticmethod
    def FREEZE(slot_id):
        return ClientParameterMapping(
            name = "Freeze " + str(slot_id),
            set = KemperNRPNMessage(
                _NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
                _NRPN_ADDRESS_PAGE_FREEZE,
                KemperEffectSlot.NRPN_FREEZE_SLOT_PARAMETER_ADDRESSES[slot_id]
            ),
            request = KemperNRPNMessage(               
                _NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                _NRPN_ADDRESS_PAGE_FREEZE,
                KemperEffectSlot.NRPN_FREEZE_SLOT_PARAMETER_ADDRESSES[slot_id]
            ),
            response = KemperNRPNMessage(               
                _NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER, 
                _NRPN_ADDRESS_PAGE_FREEZE,
                KemperEffectSlot.NRPN_FREEZE_SLOT_PARAMETER_ADDRESSES[slot_id]
            )
        )

    # Effect Button I-IIII (set only). num must be a number (1 to 4).
    def EFFECT_BUTTON(num): 
        return ClientParameterMapping(
            name = "Effect Button " + repr(num),
            set = ControlChange(
                _CC_EFFECT_BUTTON_I + (num - 1),
                0
            )
        )

    # Rig name (request only)
    RIG_NAME = ClientParameterMapping(
        name = "Rig Name",
        request = KemperNRPNMessage(               
            _NRPN_FUNCTION_REQUEST_STRING_PARAMETER,             
            _NRPN_ADDRESS_PAGE_STRINGS,
            _NRPN_STRING_PARAMETER_ID_RIG_NAME
        ),
        response = KemperNRPNMessage(
            _NRPN_FUNCTION_RESPONSE_STRING_PARAMETER, 
            _NRPN_ADDRESS_PAGE_STRINGS,
            _NRPN_STRING_PARAMETER_ID_RIG_NAME
        ),
        type = KemperMidiValueProvider.PARAMETER_TYPE_STRING
    )

    # Rig date (request only)
    RIG_DATE = ClientParameterMapping(
        name = "Rig Date",
        request = KemperNRPNMessage(               
            _NRPN_FUNCTION_REQUEST_STRING_PARAMETER, 
            _NRPN_ADDRESS_PAGE_STRINGS,
            _NRPN_STRING_PARAMETER_ID_RIG_DATE
        ),
        response = KemperNRPNMessage(
            _NRPN_FUNCTION_RESPONSE_STRING_PARAMETER, 
            _NRPN_ADDRESS_PAGE_STRINGS,
            _NRPN_STRING_PARAMETER_ID_RIG_DATE
        ),
        type = KemperMidiValueProvider.PARAMETER_TYPE_STRING
    )

    # Switch tuner mode on/off (no receive possible when not in bidirectional mode)
    TUNER_MODE_STATE = ClientParameterMapping(
        name = "Tuner Mode",
        set = ControlChange(
            _CC_TUNER_MODE, 
            0    # Dummy value, will be overridden
        ),
        response = KemperNRPNMessage(
            0x01,
            0x7f,
            0x7e
        )
    )

    # Tuner note (only sent in bidirectional mode)
    TUNER_NOTE = ClientParameterMapping(
        name = "Tuner Note",
        response = KemperNRPNMessage(
            0x01,
            0x7d,
            0x54
        )
    )

    # Tuner deviance from "in tune" (only sent in bidirectional mode)
    TUNER_DEVIANCE = ClientParameterMapping(
        name = "Tuner Deviance",
        response = KemperNRPNMessage(
            0x01,
            0x7c,
            0x0f
        )
    )

    # Switch tuner mode on/off (no receive possible!)
    TAP_TEMPO = ClientParameterMapping(
        name = "Tap Tempo",
        set = ControlChange(
            _CC_TAP_TEMPO, 
            0    # Dummy value, will be overridden
        )
    )

    # Rig volume
    RIG_VOLUME = ClientParameterMapping(
        name = "Rig Volume",
        set = KemperNRPNMessage(
            _NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
            _NRPN_ADDRESS_PAGE_RIG_PARAMETERS,
            _NRPN_RIG_PARAMETER_VOLUME
        ),
        request = KemperNRPNMessage(
            _NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER,
            _NRPN_ADDRESS_PAGE_RIG_PARAMETERS,
            _NRPN_RIG_PARAMETER_VOLUME
        ),
        response = KemperNRPNMessage(
            _NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
            _NRPN_ADDRESS_PAGE_RIG_PARAMETERS,
            _NRPN_RIG_PARAMETER_VOLUME
        )
    )

    # Amp name (request only)
    AMP_NAME = ClientParameterMapping(
        name = "Amp Name",
        request = KemperNRPNMessage(               
            _NRPN_FUNCTION_REQUEST_STRING_PARAMETER, 
            _NRPN_ADDRESS_PAGE_STRINGS,
            _NRPN_STRING_PARAMETER_ID_AMP_NAME
        ),
        response = KemperNRPNMessage(
            _NRPN_FUNCTION_RESPONSE_STRING_PARAMETER, 
            _NRPN_ADDRESS_PAGE_STRINGS,
            _NRPN_STRING_PARAMETER_ID_AMP_NAME
        ),
        type = KemperMidiValueProvider.PARAMETER_TYPE_STRING
    )

    # Amp on/off
    AMP_STATE = ClientParameterMapping(
        name = "Amp Status",
        set = KemperNRPNMessage(
            _NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
            _NRPN_ADDRESS_PAGE_AMP,
            _NRPN_AMP_PARAMETER_STATE
        ),
        request = KemperNRPNMessage(
            _NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER,
            _NRPN_ADDRESS_PAGE_AMP,
            _NRPN_AMP_PARAMETER_STATE
        ),
        response = KemperNRPNMessage(
            _NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
            _NRPN_ADDRESS_PAGE_AMP,
            _NRPN_AMP_PARAMETER_STATE
        )
    )

    # Cab name (request only)
    CABINET_NAME = ClientParameterMapping(
        name = "Cab Name",
        request = KemperNRPNMessage(               
            _NRPN_FUNCTION_REQUEST_STRING_PARAMETER, 
            _NRPN_ADDRESS_PAGE_STRINGS,
            _NRPN_STRING_PARAMETER_ID_CABINET_NAME
        ),
        response = KemperNRPNMessage(
            _NRPN_FUNCTION_RESPONSE_STRING_PARAMETER, 
            _NRPN_ADDRESS_PAGE_STRINGS,
            _NRPN_STRING_PARAMETER_ID_CABINET_NAME
        ),
        type = KemperMidiValueProvider.PARAMETER_TYPE_STRING
    )
    
    # Cab on/off
    CABINET_STATE = ClientParameterMapping(
        name = "Cab Status",
        set = KemperNRPNMessage(
            _NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
            _NRPN_ADDRESS_PAGE_CABINET,
            _NRPN_CABINET_PARAMETER_STATE
        ),
        request = KemperNRPNMessage(
            _NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER,
            _NRPN_ADDRESS_PAGE_CABINET,
            _NRPN_CABINET_PARAMETER_STATE
        ),
        response = KemperNRPNMessage(
            _NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
            _NRPN_ADDRESS_PAGE_CABINET,
            _NRPN_CABINET_PARAMETER_STATE
        )
    )

    NEXT_BANK = ClientParameterMapping(
        name = "Next Bank",
        set = ControlChange(
            _CC_BANK_INCREASE,
            0    # Dummy value, will be overridden
        )
    )

    PREVIOUS_BANK = ClientParameterMapping(
        name = "Prev Bank",
        set = ControlChange(
            _CC_BANK_DECREASE,
            0    # Dummy value, will be overridden
        )
    )

    # Selects a rig inside the current bank. Rig index must be in range [0..4]
    @staticmethod
    def RIG_SELECT(rig):
        return ClientParameterMapping(
            name = "Rig Select",
            set = ControlChange(
                _CC_RIG_SELECT + rig,
                0    # Dummy value, will be overridden
            )
        )
    
    # Pre-selects a bank. CHanges will take effect when the next RIG_SELECT message is sent.
    # Bank index must be in range [0..124]
    BANK_PRESELECT = ClientParameterMapping(
        name = "Bank Preselect",
        set = ControlChange(
            _CC_BANK_PRESELECT,
            0    # Dummy value, will be overridden
        )
    )

    # Used for state sensing in bidirection communication
    BIDIRECTIONAL_SENSING = ClientParameterMapping(
        response = KemperNRPNExtendedMessage(
            0x7e,
            [
                0x7f
            ]
        )
    ) 
    

####################################################################################################################


_PARAMETER_SET_2 = [
    KemperMappings.EFFECT_TYPE(KemperEffectSlot.EFFECT_SLOT_ID_A),
    KemperMappings.EFFECT_STATE(KemperEffectSlot.EFFECT_SLOT_ID_A),

    KemperMappings.EFFECT_TYPE(KemperEffectSlot.EFFECT_SLOT_ID_B),
    KemperMappings.EFFECT_STATE(KemperEffectSlot.EFFECT_SLOT_ID_B),

    KemperMappings.EFFECT_TYPE(KemperEffectSlot.EFFECT_SLOT_ID_C),
    KemperMappings.EFFECT_STATE(KemperEffectSlot.EFFECT_SLOT_ID_C),

    KemperMappings.EFFECT_TYPE(KemperEffectSlot.EFFECT_SLOT_ID_D),
    KemperMappings.EFFECT_STATE(KemperEffectSlot.EFFECT_SLOT_ID_D),

    KemperMappings.EFFECT_TYPE(KemperEffectSlot.EFFECT_SLOT_ID_X),
    KemperMappings.EFFECT_STATE(KemperEffectSlot.EFFECT_SLOT_ID_X),

    KemperMappings.EFFECT_TYPE(KemperEffectSlot.EFFECT_SLOT_ID_MOD),
    KemperMappings.EFFECT_STATE(KemperEffectSlot.EFFECT_SLOT_ID_MOD),

    KemperMappings.RIG_NAME,

    KemperMappings.TUNER_MODE_STATE,
    KemperMappings.TUNER_NOTE,
    KemperMappings.TUNER_DEVIANCE         
]

_SELECTED_PARAMETER_SET_ID = const(0x02)
_SELECTED_PARAMETER_SET = _PARAMETER_SET_2


# Implements the internal Kemper bidirectional communication protocol
class KemperBidirectionalProtocol: #(BidirectionalProtocol):
    
    _STATE_OFFLINE = 10   # No commmunication initiated
    _STATE_RUNNING = 20   # Bidirectional communication established

    def __init__(self, time_lease_seconds):
        self.state = self._STATE_OFFLINE
        self._time_lease_encoded = self._encode_time_lease(time_lease_seconds)

        # This is the reponse template for the status sensing message the Profiler sends every
        # about 500ms.
        self._mapping_sense = KemperMappings.BIDIRECTIONAL_SENSING

        # Re-send the beacon after half of the lease time have passed
        self.resend_period = PeriodCounter(time_lease_seconds * 1000 * 0.5)

        # Period for initial beacons (those shall not be sent too often)
        self.init_period = PeriodCounter(5000)

        # Period after which communication will be regarded as broken when no sensing message comes in
        # (the device sends this roughly every 500ms so we wait 1.5 seconds which should be sufficient)
        self.sensing_period = PeriodCounter(1500)
        self.sensing_period.reset()

        self.debug = False   # This is set by the BidirectionalClient constructor
        self._count_relevant_messages = 0
        self._has_been_running = False
        
    # Called before usage, with a midi handler.
    def init(self, midi, client):
        self._midi = midi  
        self._client = client

    # Must return (boolean) if the passed mapping is handled in the bidirectional protocol
    def is_bidirectional(self, mapping):
        return mapping in _SELECTED_PARAMETER_SET

    # Must return a color representation for the current state
    def get_color(self):
        return Colors.GREEN if self.state == self._STATE_RUNNING else Colors.RED
 
    # Must return (boolean) if the passed mapping should feed back the set value immediately
    # without waiting for a midi message.
    def feedback_value(self, mapping):
        return self.is_bidirectional(mapping)

    # Initialize the communication and keeps it alive when time lease exceeds
    def update(self):
        if self.state == self._STATE_OFFLINE:
            if self.init_period.exceeded:
                if self.debug:
                    self._print("Initialize")

                if self._has_been_running:
                    self._client.notify_connection_lost()                    

                self._send_beacon(
                    init = True
                )

        elif self.state == self._STATE_RUNNING:
            if self.sensing_period.exceeded:
                self.state = self._STATE_OFFLINE

                if self.debug:
                    self._print("Lost connection")                

            elif self.resend_period.exceeded:
                if self.debug:
                    self._print("Send keep-alive message")

                self._send_beacon()

    # Receive sensing messages and re-init (with init = 1 again) when they stop appearing for longer then 1 second
    def receive(self, midi_message):
        if not isinstance(midi_message, SystemExclusive):
            return
               
        # Compare manufacturer IDs
        if midi_message.manufacturer_id != self._mapping_sense.response.manufacturer_id:
            return False
        
        if self.debug:
            self._count_relevant_messages += 1

        # Check if the message belongs to the status sense mapping. The following have to match:
        #   2: function code, (0x7e)
        #   3: instance ID,   (0x00)
        #   4: address page   (0x7f)
        #
        # The first two values are ignored (the Kemper MIDI specification implies this would contain the product type
        # and device ID as for the request, however the device just sends two zeroes)
        if midi_message.data[2:5] != self._mapping_sense.response.data[2:5]:
            return False
        
        if self.state != self._STATE_RUNNING:
            self.resend_period.reset()
            
            if self.debug:
               self._print("Connection established")

            self._has_been_running = True
            self.state = self._STATE_RUNNING

        self.sensing_period.reset()

    # Send beacon for bidirection communication
    def _send_beacon(self, init = False):
        self._midi.send(
            KemperNRPNExtendedMessage(
                0x7e,
                [
                    0x40,
                    _SELECTED_PARAMETER_SET_ID,
                    self._get_flags(
                        init = init,
                        tunemode = True
                    ),
                    self._time_lease_encoded
                ]
            )
        )

    # Encode time lease (this is done in 2 second steps for the Kemper)
    def _encode_time_lease(self, time_lease_seconds):
        return int(time_lease_seconds / 2)

    # Generates the flags byte.
    def _get_flags(self, init = False, sysex = True, echo = False, nofe = False, noctr = False, tunemode = False):
        i = 1 if init else 0
        s = 1 if sysex else 0
        e = 1 if echo else 0
        n = 1 if nofe else 0
        c = 1 if noctr else 0
        t = 1 if tunemode else 0

        return 0x00 | (i << 0) | (s << 1) | (e << 2) | (n << 3) | (c << 4) | (t << 5)

    def _print(self, msg):
        do_print("Bidirectional (" + formatted_timestamp() + "): " + msg + " (Received " + repr(self._count_relevant_messages) + ")")
        self._count_relevant_messages = 0
