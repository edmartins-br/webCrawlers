import os
import json

import re
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
from django.utils import timezone
from systemic_queries.models import SystemicQuery, SystemicQueryItem
from drivers.models import Driver, DriverXXX
from scrapper.settings import TEMP_ROOT
from drivers.models_driver_restriction import DriverRestriction


class XXXXX(BaseEngine):
    def __init__(self, item):
        print("LOG CRAW-173: __init__...")
        super().__init__(item=item)
        self.item = SystemicQueryItem.objects.get(pk=item)

        self.license = (
            DriverXXX.objects.filter(driver=self.item.driver)
            .order_by('validate')
            .last()
        )       

        self.index = "https://www.xxxxxxx.com"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--window-size=1024,1648")
        prefs = {
            "download.directory_upgrade": True,
            "download.prompt_for_download": False,
            "download.default_directory": f'{TEMP_ROOT}{item}',
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "plugins.always_open_pdf_externally": True,
        }
        chrome_options.add_argument('--kiosk-printing')
        chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(
            executable_path=binary_path, options=chrome_options
        )
    
    def execute(self):
        print("LOG CRAW-173: def execute...")
        if not self.license:
            self.item.status = 'IMPEDIDO'
            self.item.response = 'CONDUTOR SEM DADOS NECESSÁRIOS'
        elif not (self.item.driver.birth_date and self.item.driver.cpf):
            self.item.status = 'IMPEDIDO'
            self.item.response = 'CONDUTOR SEM DADOS NECESSÁRIOS'
        elif self.first_step():
            self.item.status = 'FINALIZADO'
        else:
            self.item.status = 'FINALIZADO COM ERRO'        
        self.item.save()

        return True
        
    def first_step(self):
        print("Iniciando CRAWLER...") 
        self.driver.get(self.index)   
        
        print('Inserindo Nome...')
        self.driver.find_element_by_xpath(
            '//*[@id="NOME"]'
            ).send_keys(self.item.driver.name)        
        sleep(0.5)
        
        print('Inserindo registro...')
        self.driver.find_element_by_xpath(
            '//*[@id="REGISTRO"]'
            ).send_keys(self.item.driver.main_XXX)
        sleep(0.5)

        print('Inserindo CPF...')
        self.driver.find_element_by_xpath(
            '//*[@id="CPF"]'
            ).send_keys(self.item.driver.cpf)
        sleep(0.5)

        print('Inserindo Data de Nascimento...')
        self.driver.find_element_by_xpath(
            '//*[@id="NASCIMENTO"]'
            ).send_keys(self.item.driver.birth_date)
        sleep(0.5)

        #Solve Question
        question = self.driver.find_element_by_xpath(
            '//*[@id="pergunta"]'
            ).text
        question = question.split(' ')
        
        sleep(1)
        result = int(question[2]) + int((question[4]).replace('?', ''))      
        result = str(result)          
        print(f'{question[2]} + {question[4]} = {result}')
        
        print('Inserindo resultado...')
        self.driver.find_element_by_xpath(
            '//*[@id="CODSEG"]'
            ).send_keys(result)
        sleep(1)

        print('Clicando em consultar...')
        self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div/div[2]/a[1]'
            ).click()
        sleep(1)        
        
        tags = [
            {"tag": "select", "attribute": {"class": "form-control"}, "id": "RADIOENDERECO"}
        ]

        print('Aguardando carregamento da página...')
        self.wait_for_tags(tags)        
        
        print('Armazenando endereços em lista...')
        for i in range (1, 6):
            ADDRESS = []
            ADDRESS.append(self.driver.find_element_by_xpath(
            '//*[@id="RADIOENDERECO"]/option' + [i]
            )).text
            sleep(0.5)
        
        print('Realizando tentativas de escolha do Endereço...')
        while True:
            for address_index in range(0,5) :
                print(f'Tentativa {address_index}...')
                            
                adr = self.driver.find_element_by_xpath(
                    '//*[@id="RADIOENDERECO"]/option[' + ADDRESS[address_index] + ']'
                    ).text

                if adr == ADDRESS[address_index]:
                    self.driver.find_element_by_xpath(
                    '//*[@id="RADIOENDERECO"]/option[' + ADDRESS[address_index] + ']'
                    ).click()
                else:
                    self.driver.back()
                    sleep(2)

                ADDRESS.pop(address_index)
                sleep(1)

                print('Clicando em consultar...')
                self.driver.find_element_by_xpath(
                    '//*[@id="content-update"]/div/div/div/div/a[1]'
                    ).click()
                
                sleep(2)

                html = self.driver.page_source
                print('HTML: ' + html)

                if html == '':
                    self.driver.back()
                    sleep(2)
                elif self.driver.find_element_by_xpath('/html/body/section/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[1]/td'):
                    return False
        
        print(ADDRESS)

        sleep(1)

        # Getting Information
        name = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[3]/div/p/strong[1]'
            ).text
        
        category = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[4]/div/table/tbody/tr[2]/td'
            ).text
        
        points = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[2]/td'
            ).text
        
        temporary_block = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[4]/td/div'
            ).text
        
        national_block = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[6]/td/div'
            ).text
        
        DRIVER_DATA = {"nome" : name,
                      "registro" : self.item.driver.main_XXX,                      
                      "cpf" : self.item.driver.cpf,
                      "data_nasc" : self.item.driver.birth_date,
                      "categoria" : category,
                      "pontuacao" : points,
                      "sit_bloqueio_provisorio" : temporary_block,
                      "sit_bloqueio_nacional" : national_block, 
                      }
        
        print(DRIVER_DATA)      

        pontuation = int(DRIVER_DATA['pontuacao'])
        tipo = self.driver.find_element_by_xpath('/html/body/section/div/div/div[1]/h3').text
                        
        print('Salvando pontuação...')
        self.item.driver.points = pontuation
        self.item.driver.save()

        restriction = DriverRestriction(

            query_item = self.item,
            XXX = self.license,
            date = datetime.now().replace(tzinfo=timezone.utc),
            points = int(pontuation),
            kind = tipo      
            # EXTRATO, SUSPENSÃO, CASSAÇÃO, NADA CONSTA      
        )             
        
        print('Salvando dados...')
        restriction.save()

        print('=*=*=* CONSULTA FINALIZADA =*=*=*')

        return True

    def get_response_error(self, response):
        response = re.sub('[^\w ]', '', response).strip(' ')
        if 'ocorreu um erro interno no sistema' in response.lower():
            raise Exception('erro interno do site de consulta')
        else:
            return response          
       

if __name__ == '__main__':

    crawl = XXXXX(47580)
    crawl.execute()
