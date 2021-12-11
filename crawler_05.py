import re
import os
import pdfkit
import requests
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
from ..base_engine import BaseEngine
from systemic_queries.models import SystemicQueryItem
from drivers.models import Driver, DriverCnh
from drivers.models_driver_restriction import DriverRestriction
from scrapper.settings import TEMP_ROOT
import base64


class XXXXXX(BaseEngine):
    def __init__(self, item):
        super().__init__(item=item)
        self.license = DriverCnh.objects.filter(
            driver=self.item.driver).order_by('validate').last()
        self.item = SystemicQueryItem.objects.get(pk=item)
        self.index = "http://www.xxxxxx.com"

        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument("--window-size=1024,1648")

        chrome_options.add_experimental_option('prefs', {
            # Change default directory for downloads
            "download.default_directory": TEMP_ROOT,
            "download.prompt_for_download": False,  # To auto download the file
            "download.directory_upgrade": True,
            # It will not show PDF directly in chrome
            "plugins.always_open_pdf_externally": True
        })

        self.driver = webdriver.Chrome(
            executable_path=binary_path, options=chrome_options)

    def execute(self):
        print("LOG CRAW 213 (CE)>> def execute...")
        if not self.license:
            self.item.status = 'IMPEDIDO'
            self.item.response = 'CONDUTOR SEM DADOS NECESSÁRIOS'
        elif not (self.license.cnh and self.item.driver.cpf):
            self.item.status = 'IMPEDIDO'
            self.item.response = 'CONDUTOR SEM DADOS NECESSÁRIOS'
        else:
            sucess = self.first_step()
            self.item.status = 'FINALIZADO'
            if not sucess:
                self.item.status = 'FINALIZADO COM ERRO'
        self.item.save()

        return True

    def first_step(self):
        print("LOG CRAW 213 (CE)>> Iniciando crawler...")
        self.driver.get(self.index)

        print('LOG CRAW 213 (CE)>> Armazenando aba atual...')
        original_window = self.driver.current_window_handle
        assert len(self.driver.window_handles) == 1

        print('LOG CRAW 213 (CE)>> Clicando em "SERVIÇOS"...')
        self.driver.find_element_by_css_selector('#menu-item-3120 > a').click()
        sleep(5)

        print('LOG CRAW 213 (CE)>> Trocando aba...')
        WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))

        for window_handle in self.driver.window_handles:
            if window_handle != original_window:
                self.driver.switch_to.window(window_handle)
                break
        sleep(1)

        print('LOG CRAW 213 (CE)>> Clicando em "HABILITAÇÃO"...')
        self.driver.find_element_by_xpath(
            '/html/body/div[5]/ul/li[2]/a').click()
        sleep(1)

        print('LOG CRAW 213 (CE)>> Clicando em "Emitir Nada Consta"...')
        self.driver.find_element_by_css_selector(
            '#habilitacao > div > div > div.col-md-3 > div > div.panel-body > div > a.list-group-item.list-group-item-success.nada-consta'
        ).click()
        sleep(1)

        input_cpf = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="nada_consta_cpf"]')))
        input_cpf.clear()
        cpf = (self.item.driver.cpf)
        cpf = '{}.{}.{}-{}'.format(cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])
        input_cpf.send_keys(cpf)
        print(f'LOG CRAW 213 (CE)>> CPF: {cpf}')

        input_cnh = self.driver.find_element_by_xpath(
            '//*[@id="nada_consta_numero_formulario"]')
        input_cnh.clear()
        input_cnh.send_keys(self.license.cnh)
        print('LOG CRAW 213 (CE)>> CNH: ' + self.license.cnh)

        input_cpf.click()

        sleep(2)

        # Solve captcha
        captcha_element = self.wait_for_tag("img", {"alt": "captcha"})
        captcha_element = self.driver.find_element_by_css_selector(
            '#captcha-img > img')
        encoded_string = captcha_element.screenshot_as_base64

        captcha = {
            "method": "base64",
            "key": self.captcha_token,
            "body": encoded_string
        }

        print('LOG CRAW 213 (CE)>> Enviando captcha via API (BaseEngine)')
        captcha_result = self.get_image_captcha(captcha, 20)

        print('LOG CRAW 213 (CE)>> Inserindo captcha no campo...')
        input_sec_code = self.driver.find_element_by_xpath(
            '//*[@id="nada_consta_captcha"]')
        input_sec_code.send_keys(captcha_result)
        sleep(2)

        print('LOG CRAW 213 (CE)>> Clicando em Consultar...')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#nada-consta-submit'))).click()
        sleep(2)

        # =*=*=*=*=*=*=*=*=*=* VERIFICANDO ERROS DE AUTENTICAÇÃO =*=*=*=*=*=*=*=*=*=*=*=*=

        print('LOG CRAW 213 (CE)>> Aguardando carregamento da página...')
        tags = [
            {"tag": "label", "attribute": {
                "class": "control-label msg-validacao control-label"}, "id": "erroLogin"},
            {"tag": "embed", "attribute": {
                "type": "application/pdf"}, "id": "loginSucceed"}
        ]

        tag = self.wait_for_tags(tags)

        print('LOG CRAW 213 (CE)>> Verificando posíveis erros de login...')

        if tag['id'] == "erroLogin":

            on_submit = self.driver.find_element_by_xpath(
                '//*[@id="new_nada_consta"]/div[1]/div[1]/label').text
            on_submit_code = self.driver.find_element_by_xpath(
                '//*[@id="new_nada_consta"]/div[3]/div/label').text

            if "CPF e/ou CNH inválido ou inexistente" in on_submit:
                print("=*=*=*=* ATENÇÃO: CPF e/ou CNH inválido ou inexistente. =*=*=*=*")
                response = self.fail_submit(on_submit)
                self.get_response_error(response)
                return response
            elif "código de segurança inválido" in on_submit_code:
                print("=*=*=*=* ATENÇÃO: CÓDIGO DE SEGURANÇA INVÁLIDO. =*=*=*=*")
                print('Reportando Captcha inválido para o 2captcha...')
                self.report_captcha()
                response = self.fail_submit(on_submit)
                self.get_response_error(response)
                return response

        sleep(1)
        if tag['id'] == "loginSucceed":
            print("Clicando no botão GERAR...")
            self.driver.find_element_by_xpath(
                '//*[@id="nada-consta-submit"]').click()

        # =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=

        # sleep(2)
        # print('LOG CRAW 213 (CE)>> Trocando aba...')
        # WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(3))
        # sleep(2)

        # print('LOG CRAW 213 (CE)>> Salvando PDF em TEMP ROOT...')
        # self.driver.get(self.driver.current_url)

        import PyPDF2
        from scrapper.settings import TEMP_ROOT
        print('LOG CRAW 213 (CE)>> Extraindo PDF...')
        
        pdfFileObj = open(f'{TEMP_ROOT}nada_consta_5894847', 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        
        print(pdfReader.numPages)
        pageObj = pdfReader.getPage(0)
        
        print(pageObj.extractText())
        pdfFileObj.close()

        # DRIVER_DATA = {"nome" : name,
        #               "registro" : registro,
        #               "cpf" : cpf,
        #               "data_nasc" : data_nasc,
        #               "categoria" : category,
        #               "pontuacao" : points,
        #               "situacao_bloqueio_provisorio" : temporary_block,
        #               "situacao_bloqueio_nacional" : national_block,
        #               }
        # print(DRIVER_DATA)


if __name__ == '__main__':

    crawl = XXXXXXX(47580)
    crawl.execute("36851700824", "25612454151")