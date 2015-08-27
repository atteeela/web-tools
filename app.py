#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web-tools Service
"""
import stackhut
from selenium import webdriver

class Default(stackhut.Service):
    def __init__(self):
        pass

    def renderWebpage(self, url, width, height):
        driver = webdriver.PhantomJS(stackhut.root_dir + "/phantomjs-2.0.1-bin") # or add to your PATH
        driver.set_window_size(width, height) # optional
        driver.get(url)

        driver.save_screenshot('screen.png') # save a screenshot to disk
        return stackhut.put_file('screen.png')

# export the services here
SERVICES = {"Default": Default()}
