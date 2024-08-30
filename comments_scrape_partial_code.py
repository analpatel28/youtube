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
import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pymongo

root_dir = os.path.dirname(os.path.abspath(__file__))

def get_driver():
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
    return driver



def get_comment_count_wd(driver):
    # Estimate number of comments
    num_coms = len(driver.find_elements_by_css_selector('#comment-content'))
    return num_coms


def poker_pages():
    driver = get_driver()
    video_id_list = ['msBK0fS4iWI', 'ZScJBaTUL1M']  # to be loaded from video_input .csv file

    date = datetime.today().strftime('%Y-%m-%d')

    for video_id in video_id_list:
        driver.get(f'https://www.youtube.com/watch?v={video_id}')
        time.sleep(10)
        old_height = driver.execute_script("""function getHeight() {return document.querySelector('ytd-app').scrollHeight;}return getHeight();""")
        while True:
            driver.execute_script("window.scrollTo(0, document.querySelector('ytd-app').scrollHeight)")
            time.sleep(3)
            new_height = driver.execute_script("""function getHeight() {return document.querySelector('ytd-app').scrollHeight;}return getHeight();""")

            # expand all reply chains (not working as intended yet)
            replies = driver.find_elements(By.XPATH, '//ytd-button-renderer[@id="more-replies"]/yt-button-shape/button')
            for reply in replies:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", reply)
                time.sleep(5)
                reply.click()

            columns = ['video_id',  # YT video id for the current video to which comments are attached
                       'total_video_comments',  # Total number of co mments as displayed by youtube
                       'commenter_id',  # user/channel id of commenter
                       'commenter_name',# name of commenter as displayed in (not equal to id. Youtube sometimes displays name, sometimes the user handle -> just capture what is displayed)
                       'comment_text',  # actual comment/reply
                       'comment_likes',  # the number of likes
                       'time_since_post',  # time since post (just capture string as displayed by Youtube)
                       'reply',# should take value 0 if top-level command (i.e. not a reply to any other comment), and 1 otherwise
                       'reply_to_channel_id',  #
                       'timestamp'  # timestamp marking the time of scraping the comment information
                       ]
            df_comments = pd.DataFrame(columns=columns)

            content = driver.find_elements(By.XPATH,'//ytd-comment-thread-renderer[@class="style-scope ytd-item-section-renderer"]')
            for section in content:

                comment = content[0]

                total_video_comments = 525

                commenter_id = section.find_elements(By.XPATH, './/a[@id="author-text"]')[0].get_attribute('href').strip('https://www.youtube.com/channel/')

                commenter_name = section.find_elements(By.XPATH, './/a[@id="author-text"]/span')[0].text

                comment_text = section.find_elements(By.XPATH, './/div[@id="comment-content"]')[0].text.replace('\n', '')

                comment_likes = section.find_elements(By.XPATH, './/span[@id="vote-count-middle"]')[0].get_attribute("aria-label")

                # extract the comment date
                time_since_post = section.find_elements(By.XPATH,'.//yt-formatted-string[@class="published-time-text style-scope ytd-comment-renderer"]//a[@class="yt-simple-endpoint style-scope yt-formatted-string"]')[0].text

                reply = 0  # placeholder value

                reply_to_channel_id = ''  # placeholder value, shoud be empty for top-level comments that are not in any reply-thread

                timestamp = str(datetime.fromtimestamp(datetime.now().timestamp()))

                row = [video_id, total_video_comments, commenter_id, commenter_name, comment_text, comment_likes,time_since_post, reply, reply_to_channel_id, timestamp]

                df_comments = df_comments.append(pd.Series(row, index=columns), ignore_index=True)

                # adding the replies - example for the first comment

                thread = driver.find_elements(By.XPATH, '//ytd-button-renderer[@id="more-replies"]/yt-button-shape/button')

                replies = thread[0].find_elements(By.XPATH, '//div[@id="body"]')

                if len(replies) > 1:
                    for reply in replies[1:]:
                        # extract the replier name
                        commenter_name = reply.find_elements(By.XPATH, './/a[@id="author-text"]/span')[0].text
                        commenter_id = reply.find_elements(By.XPATH, './/a[@id="author-text"]')[0].get_attribute('href').strip('https://www.youtube.com/channel/')
                        comment_text = reply.find_elements(By.XPATH, './/div[@id="comment-content"]')[0].text.replace('\n','')
                        comment_likes = reply.find_elements(By.XPATH, './/span[@id="vote-count-middle"]')[0].get_attribute("aria-label")
                        time_since_post = reply.find_elements(By.XPATH,'.//yt-formatted-string[@class="published-time-text style-scope ytd-comment-renderer"]//a[@class="yt-simple-endpoint style-scope yt-formatted-string"]')[0].text
                        reply = 1
                        reply_to_channel_id = 'UCo0VPkvFVaofwO7LAro4j'  # placeholder for example - id of top-level comment's posting user/channel at the very beginning of the current reply chain
                        row = [video_id, total_video_comments, commenter_id, commenter_name, comment_text, comment_likes,time_since_post, reply, reply_to_channel_id, timestamp]
                        df_comments = df_comments.append(pd.Series(row, index=columns), ignore_index=True)

            # Export dataframe to csv

            df_comments.to_csv(f'./{video_id}_comments1_{date}.csv', encoding='utf-8', index=False)

            # extract and store html for the entire comment section
            comments_html = driver.page_source
            with gzip.open(f'./{video_id}_comments1_{date}.txt.gz', 'wt', encoding="utf-8") as f:
                f.write(str(comments_html))
            if new_height == old_height:
                break
            old_height = new_height
if __name__ == '__main__':
    poker_pages()
