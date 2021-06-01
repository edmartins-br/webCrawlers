from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import os
import wget

driver = webdriver.Chrome('chromedriver.exe')
driver.get("https://www.instagram.com/")

userName = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))

userName.clear()
password.clear()

userName.send_keys("edmartins_br")
password.send_keys("b43b43")

login = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()

notNowSave = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Agora não')]"))).click()
notNowNotification = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Agora não')]"))).click()

searchBox = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Pesquisar']")))
searchBox.clear()
keyword = "#pepper"
searchBox.send_keys(keyword)
sleep(1)
searchBox.send_keys(Keys.ENTER)
sleep(1)
searchBox.send_keys(Keys.ENTER)
sleep(5)

driver.execute_script("window.scrollTo(0, 4000);")
images = driver.find_elements_by_tag_name('img')
images = [image.get_attribute('src') for image in images]
print(images)

path = os.getcwd()
path = os.path.join(path, keyword[1:] + "s")
os.mkdir(path)
print(path)

counter = 0
for image in images:
    save_as = os.path.join(path, keyword[1:] + str(counter) + '.jpg')
    wget.download(image, save_as)
    counter += 1
