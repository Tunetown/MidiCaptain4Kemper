#################################################################################################################################
# 
# Defines some useful MIDI mappings.
#
#################################################################################################################################
 
from adafruit_midi.control_change import ControlChange

from .KemperNRPNMessage import KemperNRPNMessage
from .KemperMidi import KemperMidi

from pyswitch.core.client.ClientParameterMapping import ClientParameterMapping


#################################################################################################################################


# Defines some useful MIDI mappings
class KemperMappings:

    # Effect slot enable/disable
    @staticmethod
    def EFFECT_SLOT_ON_OFF(slot_id):
        return ClientParameterMapping(
            name = "Effect Status " + str(slot_id),
            set = ControlChange(
                KemperMidi.CC_EFFECT_SLOT_ENABLE[slot_id], 
                0    # Dummy value, will be overridden
            ),
            request = KemperNRPNMessage(               
                KemperMidi.NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                KemperMidi.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                KemperMidi.NRPN_EFFECT_PARAMETER_ADDRESS_ON_OFF
            ),
            response = KemperNRPNMessage(
                KemperMidi.NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
                KemperMidi.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                KemperMidi.NRPN_EFFECT_PARAMETER_ADDRESS_ON_OFF
            )
        )
    
    # Effect slot type (request only)
    @staticmethod
    def EFFECT_SLOT_TYPE(slot_id):
        return ClientParameterMapping(
            name = "Effect Type " + str(slot_id),
            request = KemperNRPNMessage(               
                KemperMidi.NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                KemperMidi.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                KemperMidi.NRPN_EFFECT_PARAMETER_ADDRESS_TYPE
            ),
            response = KemperNRPNMessage(               
                KemperMidi.NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER, 
                KemperMidi.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                KemperMidi.NRPN_EFFECT_PARAMETER_ADDRESS_TYPE
            )
        )

   # Rotary speed (fast/slow)
    @staticmethod
    def ROTARY_SPEED(slot_id):
        return ClientParameterMapping(
            name = "Rotary Speed " + str(slot_id),
            set = KemperNRPNMessage(
                KemperMidi.NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
                KemperMidi.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                KemperMidi.NRPN_EFFECT_PARAMETER_ADDRESS_ROTARY_SPEED
            ),
            request = KemperNRPNMessage(               
                KemperMidi.NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                KemperMidi.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                KemperMidi.NRPN_EFFECT_PARAMETER_ADDRESS_ROTARY_SPEED
            ),
            response = KemperNRPNMessage(
                KemperMidi.NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
                KemperMidi.NRPN_SLOT_ADDRESS_PAGE[slot_id],
                KemperMidi.NRPN_EFFECT_PARAMETER_ADDRESS_ROTARY_SPEED
            )
        )

    # Freeze for slot
    @staticmethod
    def FREEZE(slot_id):
        return ClientParameterMapping(
            name = "Freeze " + str(slot_id),
            set = KemperNRPNMessage(
                KemperMidi.NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
                KemperMidi.NRPN_ADDRESS_PAGE_FREEZE,
                KemperMidi.NRPN_FREEZE_SLOT_PARAMETER_ADDRESSES[slot_id]
            ),
            request = KemperNRPNMessage(               
                KemperMidi.NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER, 
                KemperMidi.NRPN_ADDRESS_PAGE_FREEZE,
                KemperMidi.NRPN_FREEZE_SLOT_PARAMETER_ADDRESSES[slot_id]
            ),
            response = KemperNRPNMessage(               
                KemperMidi.NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER, 
                KemperMidi.NRPN_ADDRESS_PAGE_FREEZE,
                KemperMidi.NRPN_FREEZE_SLOT_PARAMETER_ADDRESSES[slot_id]
            )
        )

    # Rig name (request only)
    RIG_NAME = ClientParameterMapping(
        name = "Rig Name",
        request = KemperNRPNMessage(               
            KemperMidi.NRPN_FUNCTION_REQUEST_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_RIG_NAME
        ),
        response = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_RESPONSE_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_RIG_NAME
        ),
        type = KemperMidi.NRPN_PARAMETER_TYPE_STRING
    )

    # Rig date (request only)
    RIG_DATE = ClientParameterMapping(
        name = "Rig Date",
        request = KemperNRPNMessage(               
            KemperMidi.NRPN_FUNCTION_REQUEST_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_RIG_DATE
        ),
        response = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_RESPONSE_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_RIG_DATE
        ),
        type = KemperMidi.NRPN_PARAMETER_TYPE_STRING
    )

    # Switch tuner mode on/off (no receive possible!)
    TUNER_MODE_ON_OFF = ClientParameterMapping(
        name = "Tuner Mode",
        set = ControlChange(
            KemperMidi.CC_TUNER_MODE, 
            0    # Dummy value, will be overridden
        )
    )

    # Switch tuner mode on/off (no receive possible!)
    TAP_TEMPO = ClientParameterMapping(
        name = "Tap Tempo",
        set = ControlChange(
            KemperMidi.CC_TAP_TEMPO, 
            0    # Dummy value, will be overridden
        )
    )

    # Rig volume
    RIG_VOLUME = ClientParameterMapping(
        name = "Rig Volume",
        set = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_RIG_PARAMETERS,
            KemperMidi.NRPN_RIG_PARAMETER_VOLUME
        ),
        request = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER,
            KemperMidi.NRPN_ADDRESS_PAGE_RIG_PARAMETERS,
            KemperMidi.NRPN_RIG_PARAMETER_VOLUME
        ),
        response = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
            KemperMidi.NRPN_ADDRESS_PAGE_RIG_PARAMETERS,
            KemperMidi.NRPN_RIG_PARAMETER_VOLUME
        )
    )

    # Amp name (request only)
    AMP_NAME = ClientParameterMapping(
        name = "Amp Name",
        request = KemperNRPNMessage(               
            KemperMidi.NRPN_FUNCTION_REQUEST_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_AMP_NAME
        ),
        response = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_RESPONSE_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_AMP_NAME
        ),
        type = KemperMidi.NRPN_PARAMETER_TYPE_STRING
    )

    # Amp on/off
    AMP_ON_OFF = ClientParameterMapping(
        name = "Amp Status",
        set = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_AMP,
            KemperMidi.NRPN_AMP_PARAMETER_ON_OFF
        ),
        request = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER,
            KemperMidi.NRPN_ADDRESS_PAGE_AMP,
            KemperMidi.NRPN_AMP_PARAMETER_ON_OFF
        ),
        response = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
            KemperMidi.NRPN_ADDRESS_PAGE_AMP,
            KemperMidi.NRPN_AMP_PARAMETER_ON_OFF
        )
    )

    # Cab name (request only)
    CABINET_NAME = ClientParameterMapping(
        name = "Cab Name",
        request = KemperNRPNMessage(               
            KemperMidi.NRPN_FUNCTION_REQUEST_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_CABINET_NAME
        ),
        response = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_RESPONSE_STRING_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_STRINGS,
            KemperMidi.NRPN_STRING_PARAMETER_ID_CABINET_NAME
        ),
        type = KemperMidi.NRPN_PARAMETER_TYPE_STRING
    )
    
    # Cab on/off
    CABINET_ON_OFF = ClientParameterMapping(
        name = "Cab Status",
        set = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_SET_SINGLE_PARAMETER, 
            KemperMidi.NRPN_ADDRESS_PAGE_CABINET,
            KemperMidi.NRPN_CABINET_PARAMETER_ON_OFF
        ),
        request = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_REQUEST_SINGLE_PARAMETER,
            KemperMidi.NRPN_ADDRESS_PAGE_CABINET,
            KemperMidi.NRPN_CABINET_PARAMETER_ON_OFF
        ),
        response = KemperNRPNMessage(
            KemperMidi.NRPN_FUNCTION_RESPONSE_SINGLE_PARAMETER,
            KemperMidi.NRPN_ADDRESS_PAGE_CABINET,
            KemperMidi.NRPN_CABINET_PARAMETER_ON_OFF
        )
    )

    NEXT_BANK = ClientParameterMapping(
        name = "Next Bank",
        set = ControlChange(
            KemperMidi.CC_BANK_INCREASE,
            0    # Dummy value, will be overridden
        )
    )

    PREVIOUS_BANK = ClientParameterMapping(
        name = "Prev Bank",
        set = ControlChange(
            KemperMidi.CC_BANK_DECREASE,
            0    # Dummy value, will be overridden
        )
    )

    # Selects a rig inside the current bank. Rig index must be in range [0..4]
    @staticmethod
    def RIG_SELECT(rig):
        return ClientParameterMapping(
            name = "Rig Select",
            set = ControlChange(
                KemperMidi.CC_RIG_SELECT + rig,
                0    # Dummy value, will be overridden
            )
        )
    
    # Pre-selects a bank. CHanges will take effect when the next RIG_SELECT message is sent.
    # Bank index must be in range [0..124]
    BANK_PRESELECT = ClientParameterMapping(
        name = "Bank Preselect",
        set = ControlChange(
            KemperMidi.CC_BANK_PRESELECT,
            0    # Dummy value, will be overridden
        )
    )
    
    
