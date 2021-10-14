from dataclasses import InitVar, dataclass, field


@dataclass
class Alias:
    uid_number: int
    email_name: str
    enabled: bool = field(init=False)
    status: InitVar[int]

    def __post_init__(self, status):
        self.enabled = (status != 0)
