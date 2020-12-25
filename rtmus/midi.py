from __future__ import annotations

from typing import Iterable, List, Tuple

from rtmidi import MidiIn, MidiOut, midiconstants as c  # type: ignore

c.CLOCK = c.TIMING_CLOCK
c.START = c.SONG_START
c.STOP = c.SONG_STOP
c.SONG_POSITION = c.SONG_POSITION_POINTER

# types
EventDelta = float  # in seconds
TimeStamp = float  # time.time()
MidiPacket = List[int]
MidiMessage = Tuple[MidiPacket, EventDelta]

ALL_CHANNELS = range(16)


def get_ports(port_name: str, *, clock_source: bool = False) -> Tuple[MidiIn, MidiOut]:
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


def silence(
    port: MidiOut, *, stop: bool = True, channels: Iterable[int] = ALL_CHANNELS
) -> None:
    if stop:
        port.send_message([c.STOP])
    for channel in channels:
        port.send_message([c.CONTROL_CHANGE | channel, c.ALL_NOTES_OFF, 0])
