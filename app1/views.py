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
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
matplotlib.use('Agg')

# Create your views here.

def HomePage(request):
    return render(request, 'index.html')

def SearchPage(request):
    return render(request, 'search.html')

def ResultPage(request):
    return render(request, 'result.html')

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

def saveGraphic():
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


    barplot = sns.barplot(data=df_sorted, x='Tekrar Sayısı', y='Tag', palette='viridis')  # Renk paleti 'viridis'
    plt.xlabel('Tekrar Sayısı', fontsize=14)
    plt.ylabel('Tag', fontsize=14)
    plt.title('En Sık Geçen 50 Tag', fontsize=16)
    plt.xticks(rotation=0)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    file_path = 'static/images/grafik.png'
    if os.path.exists(file_path):
        os.remove(file_path)
    plt.savefig(file_path)
    response = FileResponse(file_path)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'

def pwFunction(veri_turu, arama_sayisi, input_degeri):
    try:
        print(1)
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app1_search_data;")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='app1_search_data';")
        add_command = """INSERT INTO app1_search_data (tag, title) VALUES (?, ?);"""
        print(12)
        print(f"{veri_turu} ve {arama_sayisi} vee {input_degeri}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            context.grant_permissions(['clipboard-read'])
            web_site = "https://www.shutterstock.com"
            print(13)
            
            populerlik = False
            # seçilen veri türüne göre url düzenlemesi 
            if veri_turu == "vector" or veri_turu =="photo" or veri_turu == "illustration":
                url = web_site + "/tr/search/" + input_degeri + "?image_type=" + veri_turu + "&page="
                populerlik = True
            elif veri_turu == "editorial image":
                url = web_site + "/tr/editorial/search/" + input_degeri
            elif veri_turu == "editorial video":
                url = web_site + "/tr/editorial/video/search/" + input_degeri
            elif veri_turu == "video":
                url = web_site + "/tr/video/search/" + input_degeri + "?page="
            print(14)

            page = context.new_page()
            print(15)
            i = 0
            sayfa_sayaci = 1
            page.goto(url + str(sayfa_sayaci))
            page.mouse.wheel(0, 10000)
            html = page.inner_html("div.mui-1nl4cpc-gridContainer-root")
            soup = BeautifulSoup(html,"html.parser")
            hrefs = [a['href'] for a in soup.find_all('a', href=True)]
            print(len(hrefs))
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

                page.goto(web_site+hrefs[i])
                page.mouse.wheel(0, 1000)
                if (populerlik):
                    if page.is_visible("strong.mui-1isu8w6-empasis"):
                        durum = page.inner_html("strong.mui-1isu8w6-empasis")
                        if durum == "En iyi seçim!":
                            arama_sayaci -= 1
                            page.get_by_role("button", name="Anahtar sözcükleri panoya kopyalayın").click()
                            titles = page.inner_html(".mui-u28gw5-titleRow > h1").split(".")
                            filtered_titles = [title.strip() for title in titles if title.strip()]
                            tags = page.evaluate("navigator.clipboard.readText()").split(',')
                            for tag, title in zip(tags, filtered_titles):
                                cursor.execute(add_command, (tag.strip(), title.strip()))
                            for tag in tags[len(filtered_titles):]:
                                cursor.execute(add_command, (tag.strip(), None))
                else:
                    arama_sayaci -= 1
                    page.get_by_role("button", name="Anahtar sözcükleri panoya kopyalayın").click()
                    titles = page.inner_html(".mui-u28gw5-titleRow > h1").split(".")
                    filtered_titles = [title.strip() for title in titles if title.strip()]
                    tags = page.evaluate("navigator.clipboard.readText()").split(',')
                    for tag, title in zip(tags, filtered_titles):
                        cursor.execute(add_command, (tag.strip(), title.strip()))
                    for tag in tags[len(filtered_titles):]:
                        cursor.execute(add_command, (tag.strip(), None))
                i+=1
            browser.close()
            conn.commit()
            conn.close()

            title = getTitle()[0] if getTitle() else None
            tags_list = getTags()
            tags_str = ', '.join([tag[0] for tag in tags_list])
            addToDatabase(veri_turu, input_degeri, title, tags_str, arama_sayisi)
            saveGraphic()
        return True
    except:
        return False
    
def downloadExcel(request):
    # Yeni dosya adı oluşturma
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H.%M.%S")
    xlsx_filename = f"veriler_{timestamp}.xlsx"

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
    workbook.save(xlsx_filename)

    # Bağlantıyı kapat
    conn.close()

    response = HttpResponse(open(xlsx_filename, 'rb').read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={xlsx_filename}'

    return response

def pw_search(request):
    if request.method == 'POST':
        dropdown_value = request.POST.get('dropdown').lower()
        number_input_value = int(request.POST.get('numberInput'))
        text_input_value = request.POST.get('textInput').lower()
        # Call your Python function with the collected values
        pwFunction(dropdown_value, number_input_value, text_input_value)
        return redirect('result')
    return redirect('search')
