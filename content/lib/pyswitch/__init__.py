#################################################################################################################################
# 
# Custom Firmware for CircuitPy based devices such as the PaintAudio MIDICaptain series, to control devices like 
# the Kemper Profiler Player, including display of Rig Name, Effect type feedback etc. which is not implemented by the PaintAudio 
# Kemper firmware (yet). The firmware has been created for Kemper devices but can easily be adapted to others (all Kemper
# specific definitions and code is located in the files beneath this one, the src folder is generic)
#
#################################################################################################################################


def init():
    # Uncomment these two lines to enable memory monitoring
    #from pyswitch.stats import Memory
    #Memory.start()

    from pyswitch.hardware.adafruit import AdafruitST7789DisplayDriver, AdafruitNeoPixelDriver, AdafruitFontLoader, AdafruitSwitch
    from pyswitch.misc import get_option

    # Initialize Display first to get console output on setup/config errors (for users who do not connect to the serial console)
    display_driver = AdafruitST7789DisplayDriver()
    display_driver.init()

    # Load global config
    from config import Config

    # NeoPixel driver 
    led_driver = AdafruitNeoPixelDriver()

    # Buffered font loader
    font_loader = AdafruitFontLoader()

    if not get_option(Config, "exploreMode"):
        # Normal operation
        from pyswitch.controller.Controller import Controller
        from pyswitch.controller.MidiController import MidiController
        from pyswitch.ui.UiController import UiController    

        # Load communication configuration
        from communication import Communication        

        # MIDI controller (does the routing)
        midi_ctr = MidiController(
            routings = Communication["midi"]["routings"]
        )

        # Optional Wrapper to include the PyMidiBridge for transfering files.
        # Disable this to save memory.
        if get_option(Config, "enableMidiBridge"):
            from pymidibridge.MidiBridgeWrapper import MidiBridgeWrapper

            midi = MidiBridgeWrapper(
                midi = midi_ctr,
                temp_file_path = '/.bridge_tmp'
            )
        else:
            midi = midi_ctr

        try:
            # Load configuration files
            from display import Splashes
            from switches import Switches

            # Controller instance (runs the processing loop and keeps everything together)
            appl = Controller(
                led_driver = led_driver, 
                protocol = get_option(Communication, "protocol", None),
                midi = midi,
                config = Config, 
                switches = Switches, 
                ui = UiController(
                    display_driver = display_driver,
                    font_loader = font_loader,
                    splash_callback = Splashes
                )
            )
            
            appl.process()

        except Exception as e:
            if get_option(Config, "enableMidiBridge"):
                midi.error(e)
            else:
                raise e

    else:
        # Explore mode: Just shows the pressed GPIO port. This can be used to determine switch assignment 
        # on unknown devices, to create layouts for the configuration.
        from pyswitch.controller.ExploreModeController import ExploreModeController
        from pyswitch.ui.UiController import UiController
        import board

        # Switch factory
        class _SwitchFactory:
            def create_switch(self, port):
                return AdafruitSwitch(port)

        appl = ExploreModeController(
            board = board, 
            switch_factory = _SwitchFactory(), 
            led_driver = led_driver, 
            ui = UiController(
                display_driver = display_driver,
                font_loader = font_loader
            )
        )

        appl.process()
        
