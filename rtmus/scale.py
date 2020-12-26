from typing import List

from attr import dataclass


@dataclass
class Scale:
    data: List[int]

    def __getitem__(self, index):
        data = self.data
        data_len = len(data)
        octave = int(index / data_len)
        offset = index % data_len
        return data[offset] + 12 * octave


ionian = Scale([0, 2, 4, 5, 7, 9, 11])
dorian = Scale([0, 2, 3, 5, 7, 8, 10])

major = ionian
minor = dorian
