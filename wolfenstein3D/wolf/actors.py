

from dataclasses import dataclass

@dataclass
class ActorState:
    shapenum: int
    name: str


class Actor:
    def __init__(self, name: str, state: ActorState, sprite_sheet):
        self.name = name
        self.state = state
        self.sprite_sheet = sprite_sheet
        self.sprite = self.sprite_sheet[self.state.shapenum]
        
    def tick(self, dt):
        pass
    
    def decide_state(self):
        return ActorState(0, "calm")
        
    def change_state(self):
        self.state = self.decide_state()
        self.sprite = self.sprite_sheet[self.state.shapenum]