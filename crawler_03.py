from time import sleep
from bs4 import BeautifulSoup
from datetime import timedelta, datetime
from dateutil import parser as dateParser
from chromedriver_py import binary_path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from django.utils import timezone
from django.core.files.base import ContentFile
from urllib3.packages.six import add_metaclass
from ..base_engine import BaseEngine
from systemic_queries.models import SystemicQueryItem
from drivers.models import Driver, DriverXXX
from drivers.models_driver_restriction import DriverRestriction
from scrapper.settings import TEMP_ROOT


class XXXXX(BaseEngine):
    def __init__(self, item):
        print("LOG CRAW-211[DF]: __init__...")
        super().__init__(item=item)
        self.item = SystemicQueryItem.objects.get(pk=item)

        self.license = (
            DriverXXX.objects.filter(driver=self.item.driver)
            .order_by('validate')
            .last()
        )       

        self.index = "https://www.xxxxxxx.com"
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument("--window-size=1024,1648")
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
        print("LOG CRAW 211 (DF): def execute...")
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
        
    def login(self):
        print("LOG CRAW 211 (DF): Iniciando CRAWLER...") 
        self.driver.get(self.index)   
        
        print('LOG CRAW 211 (DF): Inserindo Nome...')
        self.driver.find_element_by_xpath(
            '//*[@id="NOME"]'
            ).send_keys(self.item.driver.name)        
        print('LOG CRAW 211 (DF): '+self.item.driver.name)
        sleep(0.5)
        
        print('LOG CRAW 211 (DF): Inserindo registro...')
        self.driver.find_element_by_xpath(
            '//*[@id="REGISTRO"]'
            ).send_keys(self.license.XXX)
        print('LOG CRAW 211 (DF): '+self.license.XXX)
        sleep(0.5)

        print('LOG CRAW 211 (DF): Inserindo CPF...')
        self.driver.find_element_by_xpath(
            '//*[@id="CPF"]'
            ).send_keys(self.item.driver.cpf)
        print('LOG CRAW 211 (DF): '+self.item.driver.cpf)
        sleep(0.5)

        print('LOG CRAW 211 (DF): Inserindo Data de Nascimento...')
        self.driver.find_element_by_xpath(
            '//*[@id="NASCIMENTO"]'
            ).send_keys(self.item.driver.birth_date.strftime('%d%m%Y'))
        print('LOG CRAW 211 (DF): '+self.item.driver.birth_date.strftime('%d/%m/%Y'))
        sleep(0.5)

        #Solve Question
        question = self.driver.find_element_by_xpath(
            '//*[@id="pergunta"]'
            ).text
        question = question.split(' ')
        
        sleep(1)
        result = int(question[2]) + int((question[4]).replace('?', ''))      
        result = str(result)          
        print('LOG CRAW 211 (DF): ' + f'{question[2]} + {question[4]} = {result}')
        
        print('LOG CRAW 211 (DF): Inserindo resultado...')
        self.driver.find_element_by_xpath(
            '//*[@id="CODSEG"]'
            ).send_keys(result)
        sleep(1)

        print('LOG CRAW 211 (DF): Clicando em consultar...')
        self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div/div[2]/a[1]'
            ).click()
        sleep(2)        
        
    def first_step(self):
        self.login()
                
        #checking Apache Tomcat/7.0.42 - Error report        
        if self.driver.find_element_by_xpath('/html/head/title') and self.driver.find_element_by_xpath('/html/head/title').text == 'Apache Tomcat/7.0.42 - Error report':
            on_submit = self.driver.find_element_by_xpath('/html/head/title').text
            print('ATENÇÃO: ERRO DO APACHE - DAO EM FORMATO INCORRETO')
            response = self.fail_submit(on_submit)
            self.get_response_error(response)            
            return

        # Check blank page. Here a toast pops up and HTML is empty
        html = self.driver.page_source

        if html == '':
            print('ATENÇÃO: NENHUM CONDUTOR ENCONTRADO COM OS DADOS INFORMADOS!')
            self.driver.switch_to_alert().accept()
            message = 'ATENÇÃO: NENHUM CONDUTOR ENCONTRADO COM OS DADOS INFORMADOS!'
            self.driver.back()
            response = self.fail_submit(message)
            self.get_response_error(response)
            self.item.status = 'IMPEDIDO'            
            return         

        print('LOG CRAW 211 (DF): Armazenando endereços em LISTA 01...')
        ADDRESS1 = {}
        for i in range (1, 6):
            ADDRESS1[f'{i}'] = (self.driver.find_element_by_xpath(f'//*[@id="RADIOENDERECO"]/option[' + str(i) + ']').text)
            sleep(0.5)
        print(ADDRESS1)

        print('LOG CRAW 211 (DF): Clicando na última opção...')
        self.driver.find_element_by_xpath(f'//*[@id="RADIOENDERECO"]/option[5]').click()
        self.driver.find_element_by_xpath('//*[@id="content-update"]/div/div/div/div/a[1]').click()

        sleep(1)
        
        try:        
            self.driver.switch_to_alert().accept()
            print('LOG CRAW 211 (DF): PÁGINA VAZIA...')            
            self.login()     
            sleep(1)
            
            print('LOG CRAW 211 (DF): Armazenando endereços em LISTA 02...')
            ADDRESS2 = {}
            for i in range (1, 6):
                ADDRESS2[f'{i}'] = (self.driver.find_element_by_xpath(f'//*[@id="RADIOENDERECO"]/option[' + str(i) + ']').text)
                sleep(0.5)
            print(ADDRESS2)         
            sleep(2)
            print(50*('*='))

            for x in ADDRESS1:
                for y in ADDRESS2:
                    if ADDRESS1[x] == ADDRESS2[y]:
                        adr = ADDRESS1[x]
                        pos = y
            print(f'ENDEREÇO CORRETO: {adr}')            
            print(pos)
            self.driver.find_element_by_xpath(f'//*[@id="RADIOENDERECO"]/option[{pos}]').click()
            sleep(1)
            print('LOG CRAW 211 (DF): Clicando em consultar...')
            self.driver.find_element_by_xpath('//*[@id="content-update"]/div/div/div/div/a[1]').click()
            
        except:
            # ESTE PASS É APENAS PARA NÃO DAR ERRO AO ENCONTRAR O ALERT. NÃO INTERFERE EM NADA NA EXECUÇÃO DO CRAWLER
            pass
        sleep(2)
        
        label_pontos = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[1]/td'
        ).text

        pontos = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[2]/td'
        ).text
        
        label_bloqueio_prov = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[3]/td'
            ).text
        
        situacao_bloqueio_provisorio = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[4]/td/div'
            ).text
        
        label_bloqueio_nacional = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[5]/td'
            ).text

        situacao_bloqueio_nacional = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/div/div/div/div/div[5]/div/table/tbody/tr[6]/td/div'
            ).text

        tipo = self.driver.find_element_by_xpath(
            '//*[@id="content-update"]/div/div/div[1]/h3'
            ).text

        html = self.driver.page_source
        self.parse_restrictions( 
            label_pontos, 
            pontos, 
            label_bloqueio_prov, 
            situacao_bloqueio_provisorio, 
            label_bloqueio_nacional, 
            situacao_bloqueio_nacional,
            tipo
            )                
        
    def parse_restrictions(self,
            label_pontos, 
            pontos, 
            label_bloqueio_prov, 
            situacao_bloqueio_provisorio, 
            label_bloqueio_nacional, 
            situacao_bloqueio_nacional,
            tipo
            ):

            DRIVER_DATA = {label_pontos : pontos, 
                           label_bloqueio_prov : situacao_bloqueio_provisorio,
                           label_bloqueio_nacional : situacao_bloqueio_nacional}
            
            print(DRIVER_DATA)
            print('TIPO: ' + tipo)

            pontuation = int(pontos)           
                            
            print('Salvando pontuação...')
            self.item.driver.points = pontuation
            self.item.driver.save()

            restriction = DriverRestriction(

                query_item = self.item,
                XXX = self.license,
                date = datetime.now().replace(tzinfo=timezone.utc),
                points = int(pontuation),
                kind = tipo, 
                additional_information = str(DRIVER_DATA)
                # EXTRATO, SUSPENSÃO, CASSAÇÃO, NADA CONSTA      
            )

            print('Salvando dados...')
            restriction.save()

            print('=*=*=* CONSULTA FINALIZADA =*=*=*')

            return True
            
            # DRIVER_DATA = {}           
            
            # soup = BeautifulSoup(html, 'html.parser')            
            # tables = soup.find_all('table', 'table table-bordered')
            # driver_declaration = tables[1]    
            # print(driver_declaration)        
            
            # for info in driver_declaration.find_all('tbody'):
            #     rows = info.find_all('tr')
            #     for row in rows:
            #         titles = []
            #         title = row.find('td').text                                                    
            #         titles.append(title)
            #     print(titles)

            

            
                    

            #         # description = row.find('td').text                
            #         # DRIVER_DATA[title] = description
            # print(DRIVER_DATA) 

            # *=*=*=*=*=*=*=*=*=*==*=*=*=*=*=*=*=*=*=*=*=*=*=           


if __name__ == '__main__':

    crawl = XXXXX(47580)
    crawl.execute()
