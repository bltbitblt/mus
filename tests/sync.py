import sys

from attr import dataclass
from rtmidi import MidiIn, MidiOut  # type: ignore

# MIDI messages
NOTE_OFF = 0b10000000
NOTE_ON = 0b10010000
POLY_AFTERTOUCH = 0b10100000
CONTROL_CHANGE = 0b10110000
PROGRAM_CHANGE = 0b11000000
CHAN_AFTERTOUCH = 0b11010000
PITCH_BEND = 0b11100000
SYSEX = 0b11110000
SYSEX_RT = 0b11111000
PANIC = 0b11111111
CLOCK = 0b11111000
START = 0b11111010
STOP = 0b11111100
CONTINUE = 0b11111011
SONG_POSITION = 0b11110010

# MIDI special values (use with CONTROL_CHANGE)
ALL_NOTES_OFF = 0b01111011
MOD_WHEEL = 0b00000001
EXPRESSION_PEDAL = 0b00001011
SUSTAIN_PEDAL = 0b01000000
PORTAMENTO = 0b01000001
PORTAMENTO_TIME = 0b00000101

# Operations on MIDI constants
STRIP_CHANNEL = 0b11110000


def get_ports(port_name: str, *, clock_source=False):
    midi_in = MidiIn()
    midi_out = MidiOut()

    midi_in_ports = midi_in.get_ports()
    for i, midi_in_port in enumerate(midi_in_ports):
        if port_name in midi_in_port:
            try:
                midi_in.open_port(i)
                break
            except ValueError:
                raise ValueError(port_name) from None

    if clock_source:
        midi_in.ignore_types(timing=False)

    midi_out_ports = midi_out.get_ports()
    for i, midi_out_port in enumerate(midi_out_ports):
        if port_name in midi_out_port:
            try:
                midi_out.open_port(i)
            except ValueError:
                raise ValueError(port_name) from None

    return midi_in, midi_out


midi_in, midi_out = get_ports("Virtual")


@dataclass
class Echo:
    pos = 0
    on = False

    def midi_callback(self, msg, data=None):
        msg = msg[0]
        name = ""
        if msg[0] == CLOCK:
            name = "CLOCK"
            if self.on:
                if self.on and self.pos % 24 == 0:
                    print("note on")
                    midi_out.send_message([NOTE_ON, 48, 100])
                if self.on and self.pos % 24 == 12:
                    print("note off")
                    midi_out.send_message([NOTE_OFF, 48, 100])
                self.pos += 1
        elif msg[0] == START:
            name = "START"
            self.pos = 0
            self.on = True
        elif msg[0] == STOP:
            name = "STOP"
            self.on = False
        elif msg[0] == CONTINUE:
            name = "CONTINUE"
            self.on = True
        elif msg[0] == SONG_POSITION:
            name = "SONG_POSITION"
            self.pos = ((msg[2] << 7) + msg[1]) * 6
        if self.on:
            print(f"pos: {self.pos - 1} msg: {msg} name: {name}")


echo = Echo()
midi_in.ignore_types(timing=False)
midi_in.set_callback(echo.midi_callback)


sys.stdin.read()
