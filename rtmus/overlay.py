from attr import Factory, dataclass
from intervaltree import IntervalTree  # type: ignore


@dataclass
class Overlay:
    length: int
    data: IntervalTree = Factory(IntervalTree)

    def __getitem__(self, index):
        return self.data[index % self.length].pop().data


def _a_a(low, high, scale=1):
    a = Overlay(48 * scale)
    a.data[0 : 20 * scale] = low
    a.data[20 * scale : 28 * scale] = high
    a.data[28 * scale : 48 * scale] = low
    return a
