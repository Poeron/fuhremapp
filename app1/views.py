from django.shortcuts import redirect, render
from django.http import FileResponse, HttpResponse
from django.http import JsonResponse
import openpyxl
import pandas as pd
from django.db import connection
import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
import shutil
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
matplotlib.use('Agg')
from django.contrib import messages
import logging

# Define constants
WEB_SITE = "https://www.shutterstock.com"
DATABASE_NAME = "db.sqlite3"
DELETE_COMMAND = "DELETE FROM app1_search_data;"
INSERT_COMMAND = "INSERT INTO app1_search_data (tag, title, photo_id) VALUES (?, ?, ?);"

# Create your views here.

def HomePage(request):
    return render(request, 'index.html')

def SearchPage(request):
    messages_list = messages.get_messages(request)
    return render(request, 'search.html', {'messages_list': messages_list})

def getTitle ():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM app1_search_data GROUP BY title ORDER BY COUNT(title) DESC LIMIT 1;")
    value = cursor.fetchone()
    conn.close()
    return value

def getTags ():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT tag,COUNT(tag) FROM app1_search_data GROUP BY tag ORDER BY COUNT(tag) DESC LIMIT 50;")
    value = cursor.fetchall()
    conn.close()
    return value

def addToDatabase (veri_turu, value, title,  tags, arama_sayisi):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    add_command = """INSERT INTO app1_search_history (image_type, value, title, tags, search_amount, datetime) VALUES (?, ?, ?, ?, ?, ?);"""

    cursor.execute(add_command, (veri_turu, value, title, tags, arama_sayisi, datetime.now().replace(microsecond=0)))

    conn.commit()
    conn.close()

def ShowResults(request):
    #SQLite veritabanına bağlan
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    #Veriyi çek
    cursor.execute("SELECT tag, COUNT(tag) AS tekrar_sayisi FROM app1_search_data GROUP BY tag ORDER BY tekrar_sayisi DESC LIMIT 50")
    data = cursor.fetchall()

    #Veriyi pandas DataFrame'e dönüştür
    df = pd.DataFrame(data, columns=['Tag', 'Tekrar Sayısı'])

    #Veriyi tekrar sayısına göre çoktan aza doğru sırala
    df_sorted = df.sort_values(by='Tekrar Sayısı', ascending=False)  # ascending=False ile büyükten küçüğe sırala

    plt.figure(figsize=(10, 7)) 

    barplot = sns.barplot(data=df_sorted, x='Tekrar Sayısı', y='Tag', palette='viridis')  # Renk paleti 'viridis'
    plt.xlabel('Tekrar Sayısı', fontsize=14)
    plt.ylabel('Tag', fontsize=14)
    plt.title('En Sık Geçen 50 Tag', fontsize=16)
    plt.xticks(rotation=0)
    plt.yticks(fontsize=9)
    plt.tight_layout()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    folder_path = 'static/images/graphics'
    file_path = f'{folder_path}/grafik_{timestamp}.png'
    clear_folder(f'app1/{folder_path}')
    plt.savefig(f'app1/{file_path}')
    context = {'graphic_path' : file_path , 'title' : getTitle()[0]}
    return render(request, 'result.html',context)

def pwFunction(veri_turu, arama_sayisi, input_degeri):
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(DELETE_COMMAND)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='app1_search_data';")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(slow_mo=250)
            context = browser.new_context()
            context.grant_permissions(['clipboard-read'])
            
            populerlik = False
            # seçilen veri türüne göre url düzenlemesi 
            if veri_turu == "vector" or veri_turu =="photo" or veri_turu == "illustration":
                url = WEB_SITE + "/tr/search/" + input_degeri + "?image_type=" + veri_turu + "&page="
                populerlik = True
            elif veri_turu == "editorial image":
                url = WEB_SITE + "/tr/editorial/search/" + input_degeri
            elif veri_turu == "editorial video":
                url = WEB_SITE + "/tr/editorial/video/search/" + input_degeri
            elif veri_turu == "video":
                url = WEB_SITE + "/tr/video/search/" + input_degeri + "?page="

            page = context.new_page()
            i = 0
            sayfa_sayaci = 1
            page.goto(url + str(sayfa_sayaci))
            page.mouse.wheel(0, 10000)
            html = page.inner_html("div.mui-1nl4cpc-gridContainer-root")
            soup = BeautifulSoup(html,"html.parser")
            hrefs = [a['href'] for a in soup.find_all('a', href=True)]
            arama_sayaci = arama_sayisi
            while(arama_sayaci>0):
                if(i == len(hrefs)-1):
                    i = 0
                    sayfa_sayaci += 1
                    hrefs.clear()
                    page.goto(url + str(sayfa_sayaci))
                    page.mouse.wheel(0, 10000)
                    html = page.inner_html("div.mui-1nl4cpc-gridContainer-root")
                    soup = BeautifulSoup(html,"html.parser")
                    hrefs = [a['href'] for a in soup.find_all('a', href=True)]

                page.goto(WEB_SITE+hrefs[i])
                page.mouse.wheel(0, 1000)
                if (populerlik):
                    if page.is_visible("strong.mui-1isu8w6-empasis"):
                        durum = page.inner_html("strong.mui-1isu8w6-empasis")
                        if durum == "En iyi seçim!":
                            arama_sayaci -= 1
                            page.get_by_role("button", name="Anahtar sözcükleri panoya kopyalayın").click()
                            tags = page.evaluate("navigator.clipboard.readText()").split(',')
                            titles = page.inner_html(".mui-u28gw5-titleRow > h1").split(".")
                            filtered_titles = [title.strip() for title in titles if title.strip()]
                            page.get_by_role("button", name="Kodu panoya kopyalayın").click()
                            photo_id = page.evaluate("navigator.clipboard.readText()")
                            for tag, title in zip(tags, filtered_titles):
                                cursor.execute(INSERT_COMMAND, (tag.strip(), title.strip(), photo_id.strip()))
                            for tag in tags[len(filtered_titles):]:
                                cursor.execute(INSERT_COMMAND, (tag.strip(), None , None))
                else:
                    arama_sayaci -= 1
                    page.get_by_role("button", name="Anahtar sözcükleri panoya kopyalayın").click()
                    tags = page.evaluate("navigator.clipboard.readText()").split(',')
                    titles = page.inner_html(".mui-u28gw5-titleRow > h1").split(".")
                    filtered_titles = [title.strip() for title in titles if title.strip()]
                    page.get_by_role("button", name="Kodu panoya kopyalayın").click()
                    photo_id = page.evaluate("navigator.clipboard.readText()")
                    for tag, title in zip(tags, filtered_titles):
                        cursor.execute(INSERT_COMMAND, (tag.strip(), title.strip(), photo_id.strip()))
                    for tag in tags[len(filtered_titles):]:
                        cursor.execute(INSERT_COMMAND, (tag.strip(), None , None))
                i+=1
            browser.close()
            conn.commit()
            conn.close()

            #add datas to search history database
            title = getTitle()[0]
            tags_list = getTags()
            tags_str = ', '.join([tag[0] for tag in tags_list])
            addToDatabase(veri_turu, input_degeri, title, tags_str, arama_sayisi)
        return True
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return False
    
def downloadExcel(request):
    # Yeni dosya adı oluşturma
    timestamp = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    xlsx_filename = f"tagler_{timestamp}.xlsx"

    # SQLite veritabanına bağlan
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Verileri çek
    cursor.execute("SELECT tag, COUNT(tag) AS tekrar_sayisi FROM app1_search_data GROUP BY tag ORDER BY tekrar_sayisi DESC LIMIT 50")
    rows = cursor.fetchall()

    # Workbook oluştur
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    # Başlıkları yaz
    sheet.append(["Başliklar", "Tekrar Sayilari"])

    # Verileri yaz
    for tagler, tekrar_sayisi in rows:
        sheet.append([tagler, tekrar_sayisi])

    # Dosyayı kaydet
    file_path = f"app1/static/excel_files/{xlsx_filename}"
    workbook.save(file_path)

    # Bağlantıyı kapat
    conn.close()

    # Excel dosyasını HttpResponse ile gönder
    message = "Excel file generated and saved successfully!"
    return JsonResponse({'message': message})

def pw_search(request):
    if request.method == 'POST':
        dropdown_value = request.POST.get('dropdown').lower()
        number_input_value = int(request.POST.get('numberInput'))
        text_input_value = request.POST.get('textInput').lower()
        # Call your Python function with the collected values
        result = pwFunction(dropdown_value, number_input_value, text_input_value)
        if result:
            return redirect('result')
        else:
            messages.error(request, 'No results found. Please try again.')
            return redirect('search')

def clear_folder(folder_path):
    # Check if the folder exists
    if os.path.exists(folder_path):
        # Iterate through the files in the folder and delete them
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")