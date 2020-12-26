from attr import Factory, dataclass
from intervaltree import IntervalTree  # type: ignore


@dataclass
class Overlay:
    length: int
    data: IntervalTree = Factory(IntervalTree)

    def __getitem__(self, index):
        return self.data[index % self.length].pop().data


def _a_a(low, high):
    a = Overlay(48)
    a.data[0:20] = low
    a.data[20:28] = high
    a.data[28:48] = low
    return a
