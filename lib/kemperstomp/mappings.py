#################################################################################################################################
# 
# Defines some useful MIDI mappings.
#
#################################################################################################################################
 
from adafruit_midi.control_change import ControlChange

from .src.model.KemperNRPNMessage import KemperNRPNMessage
from .src.model.KemperParameterMapping import KemperParameterMapping
from .definitions import KemperMidi

#################################################################################################################################

# Defines some useful MIDI mappings
class KemperMappings:

    # Effect slot enable/disable
    @staticmethod
    def MAPPING_EFFECT_SLOT_ON_OFF(slot_id):
        return KemperParameterMapping(
            set = ControlChange(
                KemperMidi.CC_EFFECT_SLOT_ENABLE[slot_id], 
                0    # Dummy value, will be overridden
            ),
            request = KemperNRPNMessage(               
                KemperMidi.NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                KemperMidi.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                KemperMidi.NRPN_EFFECT_PARAMETER_ADDRESS_ON_OFF
            )
        )
    
    # Effect slot type (request only)
    @staticmethod
    def MAPPING_EFFECT_SLOT_TYPE(slot_id):
        return KemperParameterMapping(
            request = KemperNRPNMessage(               
                KemperMidi.NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                KemperMidi.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                KemperMidi.NRPN_EFFECT_PARAMETER_ADDRESS_TYPE
            )
        )

    # Rig name (request only)
    MAPPING_RIG_NAME = KemperParameterMapping(
        request = KemperNRPNMessage(               
            KemperMidi.NRPN_FUNCTION_REQUEST_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_RIG_NAME
        )
    )

    # Rig date (request only)
    MAPPING_RIG_DATE = KemperParameterMapping(
        request = KemperNRPNMessage(               
            KemperMidi.NRPN_FUNCTION_REQUEST_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_RIG_DATE
        )
    )

    # Switch tuner mode on/off (no receive possible!)
    TUNER_MODE_ON_OFF = KemperParameterMapping(
        set = ControlChange(
            KemperMidi.CC_TUNER_MODE, 
            0    # Dummy value, will be overridden
        ),
    )
