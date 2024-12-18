##############################################################################################################################################
# 
# Definition of actions for switches
#
##############################################################################################################################################
 
from pyswitch.hardware.Hardware import Hardware

from pyswitch.misc import Colors
from pyswitch.controller.callbacks import Callback
from pyswitch.clients.kemper import KemperActionDefinitions, KemperEffectSlot, KemperMappings, RIG_SELECT_DISPLAY_TARGET_RIG
from display import DISPLAY_HEADER_1, DISPLAY_HEADER_2, DISPLAY_HEADER_3, DISPLAY_FOOTER_1, DISPLAY_FOOTER_2, DISPLAY_FOOTER_3


#Allow change of switch behaviour based on rig name
class _EnableCallback(Callback):
    def __init__(self):
        Callback.__init__(self)
        
        self.mapping = KemperMappings.RIG_NAME()
        self.register_mapping(self.mapping)

    def enabled(self, action):
        text = self.mapping.value if self.mapping.value else "NO RIG" 
        if "FX" in text:
            return (action.id == 20)        
        else:
            return (action.id == 10)
        
_enable_callback = _EnableCallback()


# Defines the switch assignments
Switches = [

    # Switch 1 | Drive (Slot D)/FX (Slot X)
    {
        "assignment": Hardware.PA_MIDICAPTAIN_MINI_SWITCH_1,
        "actions": [
            KemperActionDefinitions.EFFECT_STATE(
                slot_id = KemperEffectSlot.EFFECT_SLOT_ID_D,
                id = 10,
                display = DISPLAY_HEADER_1,
                enable_callback = _enable_callback
            ),
            KemperActionDefinitions.EFFECT_STATE(
                slot_id = KemperEffectSlot.EFFECT_SLOT_ID_X,
                id = 20,
                display = DISPLAY_HEADER_1,
                enable_callback = _enable_callback
            ),                          
        ]
    },

    # Switch 2 | Delay
    {
        "assignment": Hardware.PA_MIDICAPTAIN_MINI_SWITCH_2,
        "actions": [
            KemperActionDefinitions.EFFECT_STATE(
                slot_id = KemperEffectSlot.EFFECT_SLOT_ID_DLY,
                display = DISPLAY_HEADER_2#,
            ),
            KemperActionDefinitions.SHOW_TEMPO(color = (50, 255, 50))
        ]
    },

    # Switch 3 | Reverb
    {
        "assignment": Hardware.PA_MIDICAPTAIN_MINI_SWITCH_3,
        "actions": [
            KemperActionDefinitions.EFFECT_STATE(
                slot_id = KemperEffectSlot.EFFECT_SLOT_ID_REV,
                # color = Colors.TURQUOISE,
                display = DISPLAY_HEADER_3
            )        
        ]
    },

    # Switch A | Rig 1 - Clean (usually)
    {
        "assignment": Hardware.PA_MIDICAPTAIN_MINI_SWITCH_A,
        "actions": [
            KemperActionDefinitions.RIG_SELECT(
                rig = 1,
                color = (85, 255, 85),
                display = DISPLAY_FOOTER_1,
                display_mode = RIG_SELECT_DISPLAY_TARGET_RIG,  
            )
        ]
    },
    
    # Switch B | Rig 3 - Crunch (usually)
    {
        "assignment": Hardware.PA_MIDICAPTAIN_MINI_SWITCH_B,
        "actions": [
            KemperActionDefinitions.RIG_SELECT(
                rig = 3,
                color = Colors.ORANGE,
                display = DISPLAY_FOOTER_2,
                display_mode = RIG_SELECT_DISPLAY_TARGET_RIG,
            )
        ]
    },

    # Switch C | Rig 4 - High Gain (usually)
    {
        "assignment": Hardware.PA_MIDICAPTAIN_MINI_SWITCH_C,
        "actions": [
            KemperActionDefinitions.RIG_SELECT(
                rig = 4,
                color = Colors.RED,
                display = DISPLAY_FOOTER_3,
                display_mode = RIG_SELECT_DISPLAY_TARGET_RIG, 
            )
        ]
    }
]