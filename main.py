#!/usr/bin/env python
import os
import json
import time
from multiprocessing import Process, Value, Array
from lib.slideshow import Slideshow

# Main function
if __name__ == "__main__":
    slideshow = Slideshow()
    
    thread_pattern = Process(target=slideshow.run_slideshow)
    thread_pattern.start()
    thread_pattern.join()
    thread_pattern.terminate()