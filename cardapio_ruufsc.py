# -*- coding: utf-8 -*-
"""
LEITURA DE MENU DO RESTAURANTE UNIVERSITÁRIO
UNIVERSIDADE FEDERAL DE SANTA CATARINA

Criado em 30 de abril de 2023

Autor: Micael Fernando Broggio

Descrição:
Este bot faz envio via email do cardápio do restaurante universitário (RU) da Universidade Federal de Santa Catarina aos destinatários pré selecionados

atualizaçoes:
-> 05 abr 2023 - envio de email alerta caso o cardapio nao esteja disponivel no site do RU para a data solicitada

python 3.9.16
selenium 4.8.0
chrome webdriver 112.0.5615.138

"""
#import
import time
import os
import requests
import PyPDF2
import smtplib
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#FUNCOES_______________________________________________________________________
#envia mensagem
def send_email(mensagem,smtp,cabecalho):
    
    #criar a mensagem do e-mail
    msg = MIMEMultipart('alternative')
    msg['From'] = cabecalho['de']
    msg['To'] = ', '.join(cabecalho['para'])
    msg['Subject'] = cabecalho['assunto']
    
    texto = MIMEText(mensagem, 'plain')
    msg.attach(texto)
    
    # Enviar o e-mail
    with smtplib.SMTP(smtp['server'], smtp['port']) as server:
        server.starttls()
        server.login(smtp['user'], smtp['password'])
        server.sendmail(cabecalho['de'], cabecalho['para'], msg.as_string())

#converte meses abreviados em numero
def convert_month(str_month):
    months2num = {'jan': '01',
        'fev': '02',
        'mar': '03',
        'abr': '04',
        'mai': '05',
        'jun': '06',
        'jul': '07',
        'ago': '08',
        'set': '09',
        'out': '10',
        'nov': '11',
        'dez': '12'}
    month_num = months2num[str_month]
    return month_num
#______________________________________________________________________________

#CONFIGURACAO EMAIL------------------------------------------------------------
#configurar os parâmetros do servidor SMTP
smtp = {'server':'smtp.gmail.com',
        'port':587,
        'user':'EMAIL REMETENTE',
        'password':'SENHA REMETENTE'}

#configurar o cabeçalho do e-mail
cabecalho = {'de':smtp['user'],
             'para':['EMAILS DESTINATARIOS'],
             'assunto':'Cardápio RU UFSC'}
#------------------------------------------------------------------------------

#abre a pagina da loja streamelements
driver = webdriver.Chrome(executable_path = "chromedriver.exe")
driver.get('https://ru.ufsc.br/ru/')
time.sleep(10)

#encontra da data atual para a pesquisa do menu
data_atual = datetime.today()
data_atual = data_atual.strftime('%d/%m/%Y')
data_atual = datetime.strptime(data_atual, '%d/%m/%Y').date()

#encontra os dados da ultima semana disponibilizada no site do RU
last_week = driver.find_element(By.CLASS_NAME, "content").get_attribute("innerText")
last_week = last_week.split("\n")
last_year = last_week[4]
last_week = last_week[6:8]

#verificacao da data atual e a semana a qual ela pertence (analise de apenas as duas ultimas semanas disponibilizadas)
cont = 0
for i in last_week:
    m = convert_month(i.split('.')[1])
    d1 = i.split('.')[0].split()[0]
    d1 = d1 + '/' + m + '/' + last_year
    d1 = datetime.strptime(d1, '%d/%m/%Y').date()
    d2 = i.split('.')[0].split()[2]
    d2 = d2 + '/' + m + '/' + last_year
    d2 = datetime.strptime(d2, '%d/%m/%Y').date()   
    if data_atual < d2 or data_atual > d1:
        last_week = i
    cont = cont + 1
id_last_week = 5 + cont
if type(last_week) == list:
    last_week = last_week[0]

#encontra os dias da ultima semana
days_week = last_week.split('.')
days_week = days_week[0].split()

#encontra dia inicial da semana
day_week_init = days_week[0]

#encontra dia final da semana
day_week_end  = days_week[2]

#encontra informacoes do ultimo mes vigente de menus
last_month = driver.find_element(By.CLASS_NAME, "content").get_attribute("innerHTML")
last_month = last_month.split('\n')
last_month = last_month[6].split('/')[5]

#cria datetimes para primeiro e ultimo dias da ultima semana
day_week_init = day_week_init + '/' + last_month + '/' + last_year
day_week_init = datetime.strptime(day_week_init, '%d/%m/%Y').date()
day_week_end = day_week_end + '/' + last_month + '/' + last_year
day_week_end = datetime.strptime(day_week_end, '%d/%m/%Y').date()

#condicional para saber se a data atual se encontra na ultima semana disponibilizada pelo site
#caso da data atual nao esteja na ultima semana
if data_atual < day_week_init or data_atual > day_week_end:
    mensagem_alerta = "O cardápio para data de hoje ainda não está disponível no site do Restaurante Universitário."
    send_email(mensagem_alerta, smtp, cabecalho)

#caso da data atual constar na ultima semana    
else:
    #extrai o url do pdf menu
    url_pdf = driver.find_element(By.CLASS_NAME, "content").get_attribute("innerHTML")
    url_pdf = url_pdf.split('\n')
    url_pdf = url_pdf[id_last_week].split('"')
    url_pdf = url_pdf[1]
    
    #requisiçao de download o pdf
    response = requests.get(url_pdf)
    
    #salva o pdf no diretorio do script
    file_name = 'cardápio.pdf'
    with open(file_name, 'wb') as f:
        f.write(response.content)
        f.close()

    #abre e realiza a leitura do pdf como todos os menus disponiveis   
    text_full = ''
    with open(file_name, 'rb') as f:
        # cria um objeto PDFReader
        reader = PyPDF2.PdfReader(f)
        
        number_of_pages = len(reader.pages)
        page = reader.pages[0]
        text = page.extract_text()
        
        text_full = text_full + text + '\n'

    #substitui os dias das semana por *** para futuro reconhecimento e separacao dos menus   
    text_full = text_full.replace('-FEIRA', '***')
    text_full = text_full.replace('SÁBADO', '***')
    text_full = text_full.replace('DOMINGO', '***')
    
    #splita o texto a partir de *** para separar os menus
    text_full2 = text_full.split('***')
    
    #iteracao entre todos os menus disponiveis da semana
    for i in range(1,len(text_full2)):

        #gera uma variavel str com o menu descrito para cada dia da semana
        data_cardapio = text_full2[i].split('\n')
        data_cardapio = data_cardapio[1].split()
        data_cardapio = data_cardapio[0]
        data_cardapio = data_cardapio.split('-')
        x = convert_month(data_cardapio[1])
        data_cardapio = str(data_cardapio[0]) + '/' + x + '/' + data_cardapio[2]
        data_cardapio = datetime.strptime(data_cardapio, '%d/%m/%y').date()
        del x

        #cria o cardapio do dia apartir da conhecidencias da data atual com a data analisada
        if (data_cardapio == data_atual):
            cardapio_day = text_full2[i].split('\n')
            cardapio_day = cardapio_day[0:5]
            cardapio_day[1] = '  ' + cardapio_day[1][10:]
            
    #cria mensagem a ser enviada        
    mensagem = 'CARDÁPIO ' + data_atual.strftime('%d/%m/%Y') + '\n' + cardapio_day[0] + '\n' + cardapio_day[1] + '\n' + cardapio_day[2] + '\n'+ cardapio_day[3] + '\n'+ cardapio_day[4]
    
    #envia a mensagem
    send_email(mensagem, smtp, cabecalho)

#remove o arquivo cardapio baixado anteriormente
os.remove(file_name)
