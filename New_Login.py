from selenium import webdriver
from APIConnect.APIConnect import APIConnect
import time
import pandas as pd
from pyotp import TOTP


class login:
    def __init__(self):
        pass


    def API(self):
        df = pd.read_csv(r'C:\Users\Lenovo\Desktop\Kiteconnect/Carry.csv')

        print(df['access_tokan'].tolist()[0])
        self.driver = webdriver.chrome.webdriver.WebDriver(
            executable_path=(r'C:\Users\Lenovo\Desktop\Kiteconnect/chromedriver.exe'))
        self.driver.get('https://www.nuvamawealth.com/api-connect/login?api_key={}'.format(df['api_key'].tolist()[0]))
        element = self.driver.find_element("xpath", '//*[@id="userID"]')
        print(element)
        # send keys
        element.send_keys(df['access_tokan'].tolist()[0])
        element_ = self.driver.find_element("xpath", '/html/body/div/div/div/div/div/div[2]/div/form/button')
        hh = element_.click()
        # import time
        time.sleep(5)
        element__ = self.driver.find_element("xpath",
                                             '/html/body/div/div/div/div/div/div[2]/div[2]/form/div[1]/div/input')
        element__.send_keys(df['password'].tolist()[0])

        totp = TOTP(df['access_Secret'].tolist()[0])
        token = totp.now()
        b = [int(x) for x in str(token)]
        print(b)
        # time.sleep(90)
        elemen = self.driver.find_element("xpath", 'html/body/div/div/div/div/div/div[2]/div[2]/form/ div[3]/input[1]')
        elemen.send_keys(b[0])

        elemen2 = self.driver.find_element("xpath", 'html/body/div/div/div/div/div/div[2]/div[2]/form/ div[3]/input[2]')
        elemen2.send_keys(b[1])

        elemen3 = self.driver.find_element("xpath", 'html/body/div/div/div/div/div/div[2]/div[2]/form/ div[3]/input[3]')
        elemen3.send_keys(b[2])

        elemen4 = self.driver.find_element("xpath", 'html/body/div/div/div/div/div/div[2]/div[2]/form/ div[3]/input[4]')
        elemen4.send_keys(b[3])

        elemen5 = self.driver.find_element("xpath", 'html/body/div/div/div/div/div/div[2]/div[2]/form/ div[3]/input[5]')
        elemen5.send_keys(b[4])

        elemen6 = self.driver.find_element("xpath", 'html/body/div/div/div/div/div/div[2]/div[2]/form/ div[3]/input[6]')
        elemen6.send_keys(b[5])

        time.sleep(2)

        button = self.driver.find_element("xpath", '/html/body/div/div/div/div/div/div[2]/div[2]/form/button')
        button.click()

        time.sleep(2)

        request_token = self.driver.current_url.split('request_id=')[1][:16]
        with open(r"C:\Users\Lenovo\Downloads\nuvarequest_token.txt", 'w') as the_file:
            the_file.write(request_token)
        self.driver.quit()


a = login()
a.API()
