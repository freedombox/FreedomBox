from dataclasses import InitVar, dataclass, field


@dataclass
class Alias:
    value: int
    name: str
    enabled: bool = field(init=False)
    status: InitVar[int]

    def __post_init__(self, status):
        self.enabled = (status != 0)
