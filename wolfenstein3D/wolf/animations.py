

class Animation:
    def __init__(self, obj, target_attr: str, duration,
                 frame_count, shapenum=0, endcallback=None, offset=0):
        # in heartbeats
        self.duration = duration
        #
        self.obj = obj
        self.target_attr = target_attr
        self.frame_count = frame_count
        self.shapenum = shapenum
        self.hb_perframe = self.duration / self.frame_count

        self.lifetime = 0
        self.endcallback = endcallback
        self.offset = offset

    def tick(self, heartbeats):
        self.lifetime += heartbeats
        if self.ended():
            if callable(self.endcallback):
                self.endcallback()
            return
        self.shapenum = self.lifetime // self.hb_perframe
        setattr(self.obj, self.target_attr, self.shapenum + self.offset)

    def ended(self) -> bool:
        return self.lifetime >= self.duration
