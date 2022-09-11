from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup 
import os
import time
import pandas as pd
import psycopg2

app = Flask(__name__)

@app.route('/get_data')
def home():
    cnt = 0
    print("app started")
    print(os.environ.get("GOOGLE_CHROME_BIN") )
    print( os.environ.get("CHROMEDRIVER_PATH"))

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)

    driver.get("https://vmslsoccer.com/webapps/common/login?returnto=spappz_live/team_page%3Freg_year=2023%26id=861")
    print("loading page...")

    elem = driver.find_element(By.NAME,"user")    
    print("done")

    elem.clear()
    elem.send_keys(os.environ.get("USER"))
    print(os.environ.get("USER"))

    elem = driver.find_element(By.NAME,"password")
    elem.clear()
    elem.send_keys(os.environ.get("PASSWORD"))

    elem = driver.find_element(By.NAME, "Cmd")
    elem.send_keys(Keys.RETURN)

    page = driver.page_source
    soup = BeautifulSoup(page)
    leage_soup = soup.find_all("div", attrs={"class": "inline" })

    while leage_soup.__len__() == 0:    
        page = driver.page_source
        soup = BeautifulSoup(page)
        leage_soup = soup.find_all("div", attrs={"class": "inline" })
        print("loading page")
        time.sleep(1)

    print("page loaded")
    driver.close()
    

    return "Flask heroku app"

if __name__ == "__main__":
    app.run()