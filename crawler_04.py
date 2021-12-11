from os import wait
from time import sleep

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from datetime import datetime
from chromedriver_py import binary_path
from selenium.webdriver.firefox.webdriver import WebDriver
from ..base_engine import BaseEngine


class XXXXXXX(BaseEngine):

    def __init__(self, item):
        super().__init__(item=item)
        # self.license = DriverCnh.objects.filter(driver=self.item.driver).order_by('validate').last()
        self.index = "http://www.xxxxxx.com"
        
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument("--window-size=1024,1648")
        
        self.driver = webdriver.Chrome(executable_path=binary_path)
    
    def execute():
        print("def execute...")
        # if not self.license:
        #     self.item.status = 'IMPEDIDO'
        #     self.item.response = 'CONDUTOR SEM DADOS NECESSÁRIOS'
        # elif not(self.item.driver.birth_date and self.license.first_cnh and self.item.driver.cpf):
        #     self.item.status = 'IMPEDIDO'
        #     self.item.response = 'CONDUTOR SEM DADOS NECESSÁRIOS'
        # elif self.first_step():
        #     self.item.status = 'FINALIZADO'
        # else:
        #     self.item.status = 'FINALIZADO COM ERRO'
        # self.item.processed_at = datetime.now()
        # self.item.save()
        
    def first_step(self, renach, cpf):
    #def first_step(self, item):
        self.driver.get(self.index)   

        print('Armazenando aba atual...')
        original_window = self.driver.current_window_handle
        assert len(self.driver.window_handles) == 1

        print('Inserindo Renach...')
        input_nome = self.driver.find_element_by_xpath('//*[@id="input_renach"]')
        input_nome.send_keys(renach)
        sleep(1)
                
        print('Inserindo CPF...')
        input_cpf = self.driver.find_element_by_xpath('//*[@id="input_cpf"]')
        input_cpf.send_keys(cpf)
        sleep(1)
                
        print('Clicando em consultar...')
        self.driver.find_element_by_xpath('//*[@id="formHabilitacao"]/div[4]/input[2]').click()
        sleep(3)

        print('Trocando aba...')
        WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))
        
        for window_handle in self.driver.window_handles:
            if window_handle != original_window:
                self.driver.switch_to.window(window_handle)
                break
        sleep(1)
        
        WebDriverWait(self.driver, 10).until(EC.title_is("Consulta RENACH"))             

        # Getting Information
        print('Adquirindo Pontuação...')
        points = self.driver.find_element_by_xpath(
            '//*[@id="div_servicos_1539"]/table/tbody/tr[3]/td[2]'
            ).text
        sleep(1)    

        print('Adquirindo Processos...')
        processo = self.driver.find_element_by_xpath(
            '//*[@id="div_servicos_1820"]/table/tbody/tr[2]/td[1]'
            ).text
        sleep(1)    
        
        print('Adquirindo Abertura...')
        abertura = self.driver.find_element_by_xpath(
            '//*[@id="div_servicos_1820"]/table/tbody/tr[2]/td[2]'
            ).text
        sleep(1)    

        print('Adquirindo Auto...')
        auto = self.driver.find_element_by_xpath(
            '//*[@id="div_servicos_1820"]/table/tbody/tr[2]/td[3]'
            ).text                       
        sleep(1)    

        DRIVER_DATA = {"renach" : renach,
                      "cpf" : cpf,                      
                      "pontos" : points,
                      "processo" : processo,
                      "abertura" : abertura,
                      "auto" : auto,                      
                      }

        print(DRIVER_DATA)                
       

if __name__ == '__main__':

    crawl = XXXXXXX(47580)
    crawl.execute()
