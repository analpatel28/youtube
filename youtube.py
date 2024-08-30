# %% Setup

import sys
import time
import os
import random
import datetime
import re
import gzip

from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from parsel import Selector

import pandas as pd
import numpy as np
import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pymongo

root_dir = os.path.dirname(os.path.abspath(__file__))


def get_comment_count_wd(driver):
    # Estimate number of comments
    num_coms = len(driver.find_elements_by_css_selector('#comment-content'))
    return num_coms


# %% Comment-scrape loop


options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--no-sandbox')
options.add_argument("--log-level=3")
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("window-size=1920x1080")
options.add_argument("--disable-notifications")
options.headless = False
driver = webdriver.Chrome(options=options)
driver.maximize_window()

video_id_list = ['msBK0fS4iWI', 'ZScJBaTUL1M']  # to be loaded from video_input .csv file

date = datetime.today().strftime('%Y-%m-%d')

for video_id in video_id_list:
    driver.get(f'https://www.youtube.com/watch?v={video_id}')
    time.sleep(5)
    old_height = driver.execute_script("""
                        function getHeight() {
                            return document.querySelector('ytd-app').scrollHeight;
                        }
                        return getHeight();
                    """)

    while True:
        driver.execute_script("window.scrollTo(0, document.querySelector('ytd-app').scrollHeight)")

        time.sleep(3)

        new_height = driver.execute_script("""
                               function getHeight() {
                                   return document.querySelector('ytd-app').scrollHeight;
                               }
                               return getHeight();
                           """)




        content = driver.find_elements(By.XPATH,'//ytd-comment-thread-renderer[@class="style-scope ytd-item-section-renderer"]')
        for section in content:
            item = {}
            total_video_comments = 525
            try:
                item['commenter_id'] = section.find_elements(By.XPATH,'.//a[@id="author-text"]')[0].get_attribute('href').strip('https://www.youtube.com/channel/')
            except:
                item['commenter_id'] = ''
            try:
                item['commenter_name'] = section.find_elements(By.XPATH,'.//a[@id="author-text"]/span')[0].text
            except:
                item['commenter_name'] = ''
            try:
                item['comment_text'] = section.find_elements(By.XPATH,'.//div[@id="comment-content"]')[0].text.replace('\n','')
            except:
                item['comment_text'] = ''
            try:
                item['comment_likes'] = section.find_elements(By.XPATH,'.//span[@id="vote-count-middle"]')[0].get_attribute("aria-label")
            except:
                item['comment_likes'] = ''
            try:
                item['time_since_post'] = section.find_elements(By.XPATH,'.//yt-formatted-string[@class="published-time-text style-scope ytd-comment-renderer"]//a[@class="yt-simple-endpoint style-scope yt-formatted-string"]')[0].text
            except:
                item['time_since_post'] = ''
            print(item)
            filename = 'youtube.csv'
            df = pd.DataFrame([item])
            if os.path.exists(filename):
                df.to_csv(filename, mode='a', index=False, header=False)
            else:
                df.to_csv(filename, mode='a', index=False, header=True)
        if new_height == old_height:
            break
        old_height = new_height

