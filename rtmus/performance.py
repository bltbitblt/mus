"""See the docstring of main()."""
from __future__ import annotations

from attr import Factory, dataclass

from .metronome import Metronome
from .midi import NOTE_OFF, NOTE_ON, MidiOut


@dataclass
class Performance:
    out: MidiOut
    metronome: Metronome = Factory(Metronome)
    last_note: int = 48

    async def play(
        self,
        out: MidiOut,
        channel: int,
        note: int,
        pulses: int,
        volume: int,
        decay: float = 0.5,
    ) -> None:
        note_on_length = int(round(pulses * decay, 0))
        rest_length = pulses - note_on_length
        out.send_message([NOTE_ON | channel, note, volume])
        await self.wait(note_on_length)
        out.send_message([NOTE_OFF | channel, note, volume])
        await self.wait(rest_length)

    async def wait(self, pulses: int) -> None:
        await self.metronome.wait(pulses)
