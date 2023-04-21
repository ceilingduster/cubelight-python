import os
import ssl
import json
import time
import uuid
import requests
import paho.mqtt.client as mqtt
from datetime import datetime
from lib.canvas import SignCanvas
from lib.patternlib import NeoPatterns, patterns
from rgbmatrix import graphics
from timeit import default_timer

class Slideshow:     
    def __init__(self, sequence_folder = 'sequences/'):
        self.sequence_folder = sequence_folder
        self.display = None
        self.start = default_timer()
        self.sequence_patterns = self.load_sequences()
        self.received_sequence = {}

        # rgbmatrix panel
        self.display = SignCanvas()

        NUMRINGS = 4
        self.rings = NeoPatterns(self.display.matrix, NUMRINGS)

        self.rings.interval[0] = 1000
        self.rings.interval[1] = 1000
        self.rings.interval[2] = 1000
        self.rings.interval[3] = 1000
        
        self.rings.activepattern[0] = patterns.NONE
        self.rings.activepattern[1] = patterns.NONE
        self.rings.activepattern[2] = patterns.NONE
        self.rings.activepattern[3] = patterns.NONE
        
        self.rings.text[0] = ""
        self.rings.text[1] = ""
        self.rings.text[2] = ""
        self.rings.text[3] = ""
        
        self.rings.pixelcolor[0] = graphics.Color(50, 50, 0)
        self.rings.pixelcolor[1] = graphics.Color(100, 100, 0)
        self.rings.pixelcolor[2] = graphics.Color(10, 10, 10)
        self.rings.pixelcolor[3] = graphics.Color(255, 0, 0)

    def on_message(self, client, userdata, message):        
        msg = json.loads(message.payload.decode("utf-8"))
        uuid_val = str(uuid.uuid4())
        self.received_sequence = msg
        self.display.abort = True
        self.start = 0

    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe("cubelight/command")

    def subscribing(self):
        self.client.on_message = self.on_message
        self.client.loop_start()

    def run_slideshow(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect

        # ssl context
        ssl_context = ssl.create_default_context()
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.tls_insecure_set(True)

        # make connection
        self.client.connect("mq.csta.cisco.com", 8443, 60)

        # listen for messages
        self.subscribing()

        # start panels black
        self.display.matrix.Fill(255, 255, 255)
        self.display.show()

        self.start_patterns()

    def start_patterns(self):
        while True:
            sequence_names = list(self.sequence_patterns.keys())
            for i in range(0, len(self.sequence_patterns)):
                if self.start == 0: # pause, and do something else
                    self.start = default_timer()
                    self.sequence = self.received_sequence
                    self.sequence_name = "MQTT"
                else:
                    self.sequence = self.sequence_patterns[sequence_names[i]][0]
                    self.sequence_name = sequence_names[i]

                self.client.publish("cubelight/updates", json.dumps(self.sequence))
                self.client.loop_read()
                self.execute_pattern(self.sequence)

    def execute_pattern(self, sequence):
        print(sequence)
        delay = sequence.get('delay') / 1000
        duration = sequence.get('duration')
        sequence_type = sequence.get('type')
        speed = sequence.get('speed')

        if 'clear' in sequence:                
            if sequence['clear'] == True:
                self.display.matrix.Fill(0, 0, 0)

        if sequence_type == 'noc-tours':
            self.display.get_noc_tours(duration)
        elif sequence_type == 'display-image':
            if 'top_image' in sequence:
                top_image = self.display.decode_img(sequence['top_image'])
                self.display.set_top_image(top_image)

            if 'top_filename' in sequence:
                top_image = self.display.image_open(sequence['top_filename'])
                self.display.set_top_image(top_image)

            if 'image' in sequence:
                img = self.display.decode_img(sequence['image'])
                if sequence.get('transition'):
                    self.display.transition(img)
                else:
                    self.display.side_image(img)        

            if 'filename' in sequence:
                img = self.display.image_open(sequence['filename'])
                if sequence.get('transition'):
                    self.display.transition(img)
                else:
                    self.display.side_image(img)        

            self.display.show()
            self.display.sleep(duration)
        elif sequence_type == 'alerts':
            print(self.received_sequence)
            self.start = default_timer()
            rings = self.received_sequence['rings']
            ringNumber = 0
            pattern_name = patterns.NONE

            for ring in rings:
                self.rings.interval[ringNumber] = ring['i']

                if ring['p'] == 1:
                    pattern_name = patterns.FILL
                elif ring['p'] == 2:
                    pattern_name = patterns.FLASHING
                elif ring['p'] == 3:
                    pattern_name = patterns.PULSING
                else:
                    pattern_name = patterns.NONE

                self.rings.activepattern[ringNumber] = pattern_name
                self.rings.text[ringNumber] = ring['text']
                self.rings.pixelcolor[ringNumber] = graphics.Color(ring['r'], ring['g'], ring['b'])
                ringNumber += 1

            while True:
                    if default_timer() - self.start >= duration: break
                    self.rings.update()
        elif sequence_type == 'infinite-scroll':
            if 'top_image' in self.sequence:
                top_image = self.display.decode_img(self.sequence['top_image'])
                self.display.set_top_image(top_image)

            if 'top_filename' in self.sequence:
                top_image = self.display.image_open(self.sequence['top_filename'])
                self.display.set_top_image(top_image)

            if 'image' in self.sequence:
                img = self.display.decode_img(self.sequence['image'])
                if self.sequence.get('transition'):
                    self.display.transition(img)
                else:
                    self.display.side_image(img)    

            if 'filename' in self.sequence:
                img = self.display.image_open(self.sequence['filename'])
                if self.sequence.get('transition'):
                    self.display.transition(img)
                else:
                    self.display.side_image(img)    

            self.display.infinite_scroll(img, sleep_seconds=delay, duration=duration)        

    def load_sequences(self):
        sequence_files = [x for x in os.listdir(
            self.sequence_folder) if x.endswith('.json')]
        sequence_data = {}
        for sequence_file in sequence_files:
            sequence_file_path = os.path.join(
                self.sequence_folder, sequence_file)
            with open(sequence_file_path, 'r') as f:
                data = json.load(f)
                for sequence_name in data.keys():
                    sequence_data[sequence_name] = data[sequence_name]
        return sequence_data

