from dataclasses import dataclass
from play.web.client import BriscolaWeb


@dataclass
class OldOidInfo:
    online_room: str | None = None
    game: BriscolaWeb | None = None
