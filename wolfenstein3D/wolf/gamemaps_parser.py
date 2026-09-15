

# return n bytes little endian from data
def get_n_bytes_LI(start, n, data: bytearray):
    result = 0
    for i in range(n):
        result <<= 8
        result |= data[start + (n - 1 - i)]
    return result


class Parser:
    def __init__(self, mapheader: bytearray, maptemp: bytearray):
        self.mapheader = mapheader
        self.maptemp = maptemp
        self.get_magic_marker()
        self.parse()

    def parse(self):
        self.level_offsets = [get_n_bytes_LI(
            2 + 4*i, 4, self.mapheader) for i in range(100)]
        self.planes = [(self.get_level_plane(i, 0), self.get_level_plane(i, 1))
                       for i in range(10)]

    def decompress(self, plane):
        decompressed = []
        i = 0
        while i < len(plane):
            entry = get_n_bytes_LI(i, 2, plane)
            if entry == self.magic_marker:
                repeat = get_n_bytes_LI(i + 2, 2, plane)
                value = get_n_bytes_LI(i + 4, 2, plane)
                decompressed += [value,] * repeat
                i += 6
                continue
            decompressed.append(entry)
            i += 2
        return decompressed

    def get_level_header(self, level_i):
        pos = self.level_offsets[level_i]
        return self.maptemp[pos: pos + 38]

    def get_level_plane(self, level_i, plane_i):
        header = self.get_level_header(level_i)
        plane_size = get_n_bytes_LI(12+2*plane_i, 2, header)
        pos = self.level_offsets[level_i] + 38
        return self.maptemp[pos: pos + plane_size]

    def get_magic_marker(self):
        self.magic_marker = get_n_bytes_LI(0, 2, self.mapheader)


WALL_TEXTURES = {
    # DOS GAMEMAPS ID : my atlas index

    0x01: 0,   # grey stone
    0x02: 0,   # grey stone
    0x03: 2,   # grey stone + flag
    0x04: 3,   # grey stone + Hitler portrait
    0x05: 9,   # blue stone + cell door
    0x06: 1,   # grey stone + eagle arch
    0x07: 9,   # cell door + skeleton -> collapsed to cell texture
    0x08: 8,   # blue stone
    0x09: 8,   # blue stone

    0x0A: 5,   # wood + eagle
    0x0B: 6,   # wood + Hitler portrait
    0x0C: 4,   # plain wood
    0x0D: 34,  # elevator entrance / closest Jaguar equivalent
    0x0E: 19,  # steel + Achtung/Verboten -> Jaguar decorated steel
    0x0F: 18,  # plain steel

    0x10: 16,  # landscape -- DAY
               # atlas 17 is the NIGHT variant

    0x11: 10,  # red brick
    0x12: 13,  # wreath/emblem wall
    # 0x13      # purple/green -- no direct Jaguar equivalent
    0x14: 11,  # red brick + eagle tapestry

    0x15: 14,  # elevator interior / rail
    0x16: 15,  # elevator interior / control panel
    0x17: 7,   # wood + iron cross
    0x18: 20,  # moss/slime stone
    # 0x19      # pink/green -- no direct Jaguar equivalent
    0x1A: 21,  # second moss/slime stone
    0x1B: 0,   # grey stone
    0x1C: 19,  # grey stone + Achtung/Verboten -> closest equivalent

    0x1D: 26,  # brown cave
    0x1E: 27,  # brown cave + blood
    0x1F: 27,  # brown cave + blood (collapsed)
    0x20: 27,  # brown cave + blood (collapsed)

    # 0x21      # Hitler stained glass -- no direct Jaguar equivalent

    0x22: 23,  # blue brick + skulls
    0x23: 30,  # grey brick
    0x24: 23,  # blue brick + swastikas -- Jaguar combines the family
    0x25: 30,  # grey brick + hole -> plain grey brick fallback
    0x26: 12,  # red/grey/brown wall
    0x27: 30,  # grey brick + crack -> plain grey brick fallback
    0x28: 22,  # plain blue brick
    0x29: 19,  # blue stone + Verboten -> closest decorated steel

    0x2A: 29,  # brown tiles
    0x2B: 30,  # grey brick + map -> plain grey brick fallback
    0x2C: 28,  # orange stone
    0x2D: 28,  # orange stone
    0x2E: 29,  # brown tiles
    0x2F: 29,  # brown tiles + banner -> brown tiles fallback
    0x30: 4,   # orange panel on wood -> wood fallback
    0x31: 3,   # grey brick + Hitler -> portrait fallback

    # Doors
    0x5A: 31,  # regular door, orientation A
    0x5B: 31,  # regular door, orientation B
    0x5C: 32,  # gold-key door
    0x5D: 32,
    0x5E: 33,  # silver-key door
    0x5F: 33,

    0x64: 34,  # elevator door
    0x65: 34,
}