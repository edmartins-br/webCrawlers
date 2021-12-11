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
from drivers.models import Driver, DriverXXX
from drivers.models_driver_restriction import DriverRestriction
from scrapper.settings import TEMP_ROOT


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

        # # TODO: Verificar os teste de impedido e/ou interrompido (validação dos dados obrigatorios no item)

    def first_step(self):

        print("LOG CRAW-173: Iniciando CRAWLER...")
        self.driver.get(self.index)
        sleep(3)

        print('Inserindo CPF...')
        self.driver.find_element_by_xpath('//*[@id="DocPrincipal"]').send_keys(
            self.item.driver.cpf
        )

        print('Inserindo Data de Nascimento...')
        self.driver.find_element_by_xpath('//*[@id="DataNascimento"]').send_keys(
            self.item.driver.birth_date.strftime('%d%m%Y')
        )

        print(self.item.driver.birth_date.strftime('%d%m%Y'))
        sleep(1)

        # Solve captcha
        captcha_element = self.wait_for_tag("img", {"id": "imgDesafio"})
        captcha_element = self.driver.find_element_by_id('imgDesafio')
        encoded_string = captcha_element.screenshot_as_base64

        captcha = {
            "method": "base64",
            "key": self.captcha_token,
            "body": encoded_string,
        }

        print('Enviando captcha via API (BaseEngine)')
        captcha_result = self.get_image_captcha(captcha, 20)

        print('Inserindo captcha no campo...')
        self.driver.find_element_by_xpath('//*[@id="CodSeguranca"]').send_keys(
            captcha_result
        )
        sleep(1)

        print('Clicando em Consultar...')
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']"))
        ).click()

        sleep(2)

        print('Aguardando carregamento da página...')
        tags = [
            {"tag": "div", "attribute": {"class": "msg msgErro"}, "id": "erroLogin"},
            {"tag": "div", "attribute": {"id": "instrucoes"}, "id": "loginSucceed"},
        ]

        tag = self.wait_for_tags(tags)

        print('Verificando posíveis erros de login...')

        if tag['id'] == "erroLogin":

            on_submit = self.driver.find_element_by_xpath('/html/body/form/div/ul/div').text

            if "Data de Nascimento invalida." in on_submit:
                print("=*=*=*=* ATENÇÃO: DATA DE NASCIMENTO INVÁLIDA. =*=*=*=*")
                response = self.fail_submit(on_submit)
                self.get_response_error(response)
                #return response
            elif "Código inválido, tente novamente." in on_submit:
                print("=*=*=*=* ATENÇÃO: CÓDIGO INVÁLIDO. =*=*=*=*")
                print('Reportando Captcha inválido para o 2captcha...')
                self.report_captcha()
                response = self.fail_submit(on_submit)
                self.get_response_error(response)
                #return response
            elif "CPF Inválido. Verifique o CPF digitado." in on_submit:
                print("=*=*=*=* ATENÇÃO: CPF INVÁLIDO. =*=*=*=*")
                response = self.fail_submit(on_submit)
                self.get_response_error(response)
                #return response

        sleep(2)
        if tag['id'] == "loginSucceed":
            print("Clicando em CERTIDÃO NEGATIVA...")
            self.driver.find_element_by_xpath('//*[@id="instrucoes"]/ul/li[1]').click()

        # Aqui não há necessidade do wait fo wait for tags,
        # uma vez que precisamos esperar apenas por uma única condição, o botão estar clicavel.
        # Uma vez carregado, automaticamente já clica, utilizando apenas WebDriverWait.

        print('Aguardando carregamento da página...')
        tags = [{"tag": "div", "attribute": {"id": "instrucoes"}, "id": "loginSucceed"},
                {"tag": "div", "attribute": {"class": "msg msgErro"}, "id": "erroLogin"}
        
        ]\

        tag = self.wait_for_tags(tags)

        if tag['id'] == "loginSucceed":

            print('Inserindo RG...')
            self.driver.find_element_by_xpath(
                '//*[@id="NumeroDocumentoIdentidade"]'
            ).send_keys(self.item.driver.rg)
            sleep(0.5)

            print('Clicando em AVANÇAR (RG)...')
            self.driver.find_element_by_xpath(
                '//*[@id="instrucoes"]/table/tbody/tr/td[1]/ul/li[3]'
            ).click()
        else:
            self.fail_submit(tag['id'])

        print('Aguardando carregamento da página...')
        tags = [
            {"tag": "div", "attribute": {"class": "msg msgErro"}, "id": "erroLogin"},
            {"tag": "form", "attribute": {"id": "form1"}, "id": "loginSucceed"}
        ]

        tag = self.wait_for_tags(tags)

        # TODO: UTILIZAR WAIT FOR TAGS PARA O ERRO E FORM 1
        if tag['id'] == "erroLogin":
            on_submit = self.driver.find_element_by_xpath('//*[@id="instrucoes"]/table/tbody/tr/td[1]/div').text
            if "Dados Pessoais não conferem com os dados da CNH" in on_submit: # before submit e trocar o html pelo elemento - self.driver.get_element_by_id
                print('ATENÇÃO: Dados Pessoais não conferem com os dados da CNH')
                self.item.status = 'IMPEDIDO'
                response = self.fail_submit(on_submit)
                return response
            elif 'Pessoa com pontuação ativa.' in on_submit:
                print('ATENÇÃO: Pessoa com pontuação ativa!')
                self.item.status = 'IMPEDIDO'
                response = self.fail_submit(on_submit)
                return response

        sleep(2)

        print('Salvando PDF...')
        html = self.driver.page_source
        return self.parse_restrictions(html)

    def parse_restrictions(self, html):

        DRIVER_DATA = {}

        soup = BeautifulSoup(html, 'html.parser')
        driver_declaration = soup.find('table', width="100%")

        for info in driver_declaration.find_all('tbody'):
            rows = info.find_all('tr')
            for row in rows:
                title = row.find('td').text
                description = row.find_all('td')[1].text
                DRIVER_DATA[title.replace('\xa0', ' ')] = description.replace(
                    '\xa0', ''
                )

        print(DRIVER_DATA)
        # print(30*'*=')
        # print(html)
        # print(30*'*=')
        html = html.replace('<head>', '<head><meta charset="utf-8">')

        html = html.replace(
            '<link rel="stylesheet" href="../css/jquery-ui.min.css" type="text/css">',
            '<link rel="stylesheet" href="https://www.xxxxxxx.com" type="text/css">',
        )

        html = html.replace(
            '<link rel="stylesheet" href="../css/EstiloDetranNet.css" type="text/css">',
            '<link rel="stylesheet" href="https://www.xxxxxxx.com" type="text/css">',
        )

        html = html.replace(
            '<script language="JavaScript" src="../js/jquery-1.11.2.min.js"></script>',
            '<script language="JavaScript" src="https://www.xxxxxxx.com"></script>',
        )

        html = html.replace(
            '<script language="JavaScript" src="../js/jquery-ui.min.js"></script>',
            '<script language="JavaScript" src="https://www.xxxxxxx.com"></script>',
        )

        html = html.replace(
            '<script language="JavaScript" src="../js/jquery.mask.min.js"></script>',
            '<script language="JavaScript" src="https://www.xxxxxxx.com"></script>',
        )

        html = html.replace('src="/', 'src="https://www.xxxxxxx.com')
        html = html.replace('href="/', 'href="https://www.xxxxxxx.com')
        html = html.replace(
            '<img src="../', '<img src="https://www.xxxxxxx.com'
        )
        html = html.replace('href="../', 'href="https://www.xxxxxxx.com')

        # from IPython import embed;embed()

        pdf_name, encoded_pdf = self.encode_html_to_pdf(html)

        pontuation = DRIVER_DATA['10. HIST. INFRAÇÕES']

        if 'NADA CONSTA' in pontuation:
            pontuation = 0

        print('Salvando pontuação...')
        self.item.driver.points = pontuation
        self.item.driver.save()

        restriction = DriverRestriction(
            query_item=self.item,
            XXX=self.license,
            date=datetime.now().replace(tzinfo=timezone.utc),
            points=int(pontuation),
            kind=DRIVER_DATA['12. IMPEDIMENTOS EXAMES']
            # EXTRATO, SUSPENSÃO, CASSAÇÃO, NADA CONSTA
        )
        restriction.file_path.save(pdf_name, ContentFile(encoded_pdf))
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
    crawl.first_step()