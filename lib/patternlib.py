import array
from enum import Enum
from rgbmatrix import graphics
from timeit import default_timer

class patterns(Enum):
    FILL = 0
    FLASHING = 1    
    NONE = 2
    PULSING = 3

class NeoPatterns:
    def __init__(self, matrix, numrings=4, numpixels=4096):
        self.matrix = matrix
        self._NUMRINGS = numrings
        self._NUMPIXELS = numpixels
        self._TOTALPIXELS = self._NUMPIXELS * self._NUMRINGS
        self._DELAYVAL = 50

        self.interval = []
        self.lastupdate = []
        self.lasttextupdate = 0
        self.index = array.array('i', [0] * self._NUMPIXELS)
        self.totalindex = 0
        self.numberpixels = []
        self.pixelcolor = []
        self.text = []
        for i in range(0, self._NUMPIXELS):
            self.pixelcolor.append(graphics.Color(0, 0, 0))

        self.activepattern = []

        for r in range(0, self._NUMRINGS):
            self.numberpixels.append(self._NUMPIXELS)
            self.interval.append(500)
            self.text.append("")
            self.activepattern.append(patterns.NONE)
            self.lastupdate.append(default_timer() * 1000)

    def update(self):
        if (((default_timer() * 1000) - self.lasttextupdate) > 2000):
            self.lasttextupdate = default_timer() * 1000
            for r in range(0, self._NUMRINGS): self.updatetext(r)


        for r in range(0, self._NUMRINGS):
            if (self.interval[r] > 0):
                if (((default_timer() * 1000) - self.lastupdate[r]) > self.interval[r]):
                    self.lastupdate[r] = default_timer() * 1000
                    self.updateled(r)
                    self.increment(r)
                    self.totalincrement()


    def updatetext(self, ringNumber):
        offsetshift = ((self.numberpixels[ringNumber] * (ringNumber+1)) - self.numberpixels[ringNumber])
        pixelnum = self.index[ringNumber] + offsetshift

        x = int(offsetshift % 256)
        y = int(offsetshift / 256) + 7
        font = graphics.Font()
        font.LoadFont("fonts/5x7.bdf")
        graphics.DrawText(self.matrix, font, x, y, self.pixeltextcolor(ringNumber), self.text[ringNumber])

    def increment(self, ringNumber):
        self.index[ringNumber] += 1
        if (self.index[ringNumber] >= self.numberpixels[ringNumber]):
            self.index[ringNumber] = 0

    def totalincrement(self):
        self.totalindex += 1
        if (self.totalindex > self._TOTALPIXELS):
            self.totalindex = 0

    def clearallpixels(self):
        self.matrix.Fill(0, 0, 0)

    def rgb_color(self, color):
        return (color.red, color.green, color.blue)

    def clearpixels(self, ringNumber):
        startpixel = ((self.numberpixels[ringNumber] * (ringNumber+1)) - self.numberpixels[ringNumber])
        endpixel = startpixel + self.numberpixels[ringNumber] - 1

    def updateled(self, ringNumber):
        offsetshift = ((self.numberpixels[ringNumber] * (ringNumber+1)) - self.numberpixels[ringNumber])
        pixelnum = self.index[ringNumber] + offsetshift

        if self.activepattern[ringNumber] == patterns.FLASHING:
            for i in range(offsetshift, (offsetshift + self.numberpixels[ringNumber])):
                x = int(i % 256)
                y = int(i / 256)

                if ((self.index[ringNumber] % 2) == 1):
                    self.matrix.SetPixel(x + 64, y, 0, 0, 0)
                else:
                    c = self.pixelcolor[ringNumber]
                    self.matrix.SetPixel(x + 64, y, c.red, c.green, c.blue)
        elif self.activepattern[ringNumber] == patterns.FILL:
            for i in range(offsetshift, (offsetshift + self.numberpixels[ringNumber])):
                x = int(i % 256)
                y = int(i / 256)

                c = self.pixelcolor[ringNumber]
                self.matrix.SetPixel(x + 64, y, c.red, c.green, c.blue)            
        elif self.activepattern[ringNumber] == patterns.PULSING:
            for i in range(offsetshift, (offsetshift + self.numberpixels[ringNumber]) - 1):
                x = int(i % 256)
                y = int(i / 256)
                c = self.pixelcolor[ringNumber]

                #print(c.red, c.green, c.blue)
                if self.index[ringNumber] >= 15:
                    self.index[ringNumber] = 0

                red = self.colormax(c.red + round(self.index[ringNumber] * 20))
                green = self.colormax(c.green + round(self.index[ringNumber] * 20))
                blue = self.colormax(c.blue + round(self.index[ringNumber] * 20))

                self.matrix.SetPixel(x + 64, y, red, green, blue)       

    def pixeltextcolor(self, ringNumber):
        return graphics.Color(200, 200, 255)
        
    def colormax(self, value):
        return max(0, min(value, 255))