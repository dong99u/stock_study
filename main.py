import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}

def set_dataframe(df: object, arr_img_list: list) -> object:
    def add_icon(x):
        if x != 0.0:
            arr_icon = arr_img_list.pop(0)
            if 'up' in arr_icon:
                return f'+{x}'
            elif 'down' in arr_icon:
                return f'-{x}'


        return f'{x}'

    df.rename(columns={'N':'순위'}, inplace=True)
    
    df.reset_index(drop=False, inplace=True)
    del df['index']

    df['전일비'] = df['전일비'].apply(add_icon)
    
    return df

def get_company_code(url: str) -> list:
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'lxml')

    return

def market_cap():

    # 옵션 생성
    options = webdriver.ChromeOptions()
    # 창 숨기는 옵션 추가
    options.add_argument("headless")

    # driver 실행
    driver = webdriver.Chrome('C:/Users/parkdongkyu/Desktop/Hwibong_project/chromedriver.exe', options=options)

    url = 'https://finance.naver.com/sise/sise_market_sum.naver?&page='
    driver.get(url)

    checkboxes = driver.find_elements(By.NAME, 'fieldIds')
    for box in checkboxes:
        if box.is_selected():
            box.click()

    items_to_select = ['영업이익', '자산총계', '매출액', '전일거래량']
    for box in checkboxes:
        parent = box.find_element(By.XPATH, '..')
        label = parent.find_element(By.TAG_NAME, 'label')
        if label.text.strip() in items_to_select:
            box.click()

    btn_apply = driver.find_element(By.XPATH, '//*[@id="contentarea_left"]/div[2]/form/div/div/div/a[1]')
    btn_apply.click()

    df = pd.DataFrame()
    arr_img_list = []

    PAGES = 3

    for idx in range(1, PAGES):
        driver.get(url + str(idx))
        
        df_temp = pd.read_html(driver.page_source)[1]
        df_temp.dropna(axis='index', how='all', inplace=True)
        df_temp.dropna(axis='columns', how='all', inplace=True)
        if len(df_temp) == 0:
            break
        df = pd.concat([df, df_temp])

        items = driver.find_elements(By.XPATH, '//div[@class="box_type_l"]/table[1]/tbody/tr[@*]/td[4]/img')
        for item in items:
            arr_img_list.append(item.get_attribute('alt'))
        company_href_list = []
        for obj in driver.find_element(By.CLASS_NAME, 'box_type_l').find_elements(By.TAG_NAME, 'a'):
            company_href_list.append(obj.get_attribute('href'))
            
    df = set_dataframe(df, arr_img_list)

    return df, len(df.columns), company_href_list

def last_search_items():
    try:
        url = "https://finance.naver.com/sise/lastsearch2.naver"
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        df = pd.read_html(res.text)[1]
        df.dropna(axis='index', how='all', inplace=True)
        df.dropna(axis='columns', how='all', inplace=True)
        
        arr_img_list = []
        for arr_img in soup.find('div', {'class': 'box_type_l'}).find_all('img'):
            arr_img_list.append(arr_img['src'])


        company_code_list = []
        for tag in soup.find('div', 'box_type_l').find_all('a', 'tltle'):
            company_code_list.append(tag['href'].split('=')[1])

        df = set_dataframe(df, arr_img_list)

        return df, company_code_list

    except Exception as ex:
        print(f'{ex} 오류가 발생했습니다.')

def day_sise(company_code):
    url = f'https://finance.naver.com/item/sise.naver?code={company_code}'
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')
    company_title = soup.find('div', 'wrap_company').find('a').get_text()

    PAGES = 7

    df = pd.DataFrame()
    for page in range(1, PAGES):
        url = f'https://finance.naver.com/item/sise_day.naver?code={company_code}&page={page}'
        res = requests.get(url, headers=headers)

        df_temp = pd.read_html(res.text)[0]
        df_temp.dropna(axis='index', how='all', inplace=True)
        df_temp.set_index('날짜', inplace=True)
        
        df = pd.concat([df, df_temp])
    df.reset_index(drop=False, inplace=True)
    return company_title, df

app = Flask(__name__)

@app.route('/')
def index():

    return render_template('index.html')

@app.route('/marketcap')
def marketcap():
    df, length_df = market_cap()
    return render_template('market_cap.html', df=df, length_df=length_df)

@app.route('/last')
def last_search():
    df, company_code_list = last_search_items()
    return render_template('last_search.html', df=df, length_df=len(df.columns), company_code_list=company_code_list)

@app.route('/last/<companycode>')
def show_day_sise(companycode):
    company_title, df = day_sise(companycode)
    labels = [lab for lab in df['날짜']]
    values = [val for val in df['종가']]


    return render_template('company.html', df=df, company_title=company_title, labels=labels, values=values)

app.run(debug=True)