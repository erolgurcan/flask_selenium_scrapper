from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup 
import os
import time
import pandas as pd
import psycopg2

app = Flask(__name__)

@app.route('/')
def home():
    cnt = 0
    print("app started")
    print(os.environ.get("GOOGLE_CHROME_BIN") )
    print( os.environ.get("CHROMEDRIVER_PATH"))

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)

    driver.get("https://vmslsoccer.com/webapps/common/login?returnto=spappz_live/team_page%3Freg_year=2023%26id=861")
    print("loading page...")
    time.sleep(10)
    elem = driver.find_element(By.NAME,"user")    
    print("done")

    elem.clear()
    elem.send_keys(os.environ.get("USER"))
    print(os.environ.get("USER"))

    elem = driver.find_element(By.NAME,"password")
    elem.clear()
    elem.send_keys(os.environ.get("PASSWORD"))

    elem = driver.find_element(By.NAME, "Cmd")
    elem.send_keys(Keys.RETURN)

    page = driver.page_source
    soup = BeautifulSoup(page)
    leage_soup = soup.find_all("div", attrs={"class": "inline" })

    while leage_soup.__len__() == 0:    
        page = driver.page_source
        soup = BeautifulSoup(page)
        leage_soup = soup.find_all("div", attrs={"class": "inline" })
        print("loading page")
        time.sleep(1)

    print("page loaded")
    driver.close()
    
    team_header = list()


    for i in leage_soup:
        if str(i).__contains__("League Standings"):
            
            table_head = i.find("tr", attrs={"class", "colhead"}).find_all("td")
            for t in table_head:
                team_header.append(t.get_text())      
                df_merge = pd.DataFrame(columns=team_header)   
                
            for k in i.find("tbody").find("table").find("tbody").children:
                if ( len(k) > 1 ): 
                    row = list()
                    ind = 0
                    for k2 in k:
                        if ind == 0:                        
                            pass
                        ind += 1
                        print(k2.get_text())
                        row.append(k2.get_text().replace(" ", ""))
                    row_dict = dict( zip( team_header, row ) )
                    df_temp = pd.DataFrame.from_dict(row_dict, orient="index")
                    df_temp = df_temp.transpose()                    
                    df_merge = pd.concat([df_merge, df_temp], sort= False)  
                    
            division = i.find( "div", attrs={ "class": "titlebar" } )
            division_num = division.get_text()        
                

    print("Standing data retrieved...")

    database = os.environ.get("DATABASE")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    host = os.environ.get("HOST")
    port = "5432"

    conn = psycopg2.connect(database=database, user = user, password = password, host = host, port = port)
    cur = conn.cursor()
    
    print("Connected to the db")

    cur.execute( "select * from standing_table " )
    rows = cur.fetchall()

    cur.execute( " delete from standing_table where league  = 'Vancouver Metro Soccer League'")
    conn.commit()

    for i in range(1, len(df_merge)):
        standing = i
        team_name = df_merge["Team"].iloc[i]
        gp = df_merge["GP"].iloc[i]
        w = df_merge["W"].iloc[i]
        d = df_merge["D"].iloc[i]
        l = df_merge["L"].iloc[i]
        gf = df_merge["GF"].iloc[i]
        ga = df_merge["GA"].iloc[i]
        gd = df_merge["GD"].iloc[i]
        pts = df_merge["PTS"].iloc[i]
        league = "Vancouver Metro Soccer League"
        season = 2022
        cur.execute( " insert into standing_table ( standing, team_name, gp, won, draw, lost, gf, ga, gd, pts, league, league_season  ) \
        values (" + "'" + str(standing) + "'" + "," + "'" + str(team_name) + "'" + "," +  str(gp) + "," + str(w) + "," + str(d) + "," + str(l) + "," + str(gf) + "," + str(ga) + "," +  str(gd) + "," + str(pts) + "," + "'"  + str(league) +"'"  + "," + str(season) +')') 
        conn.commit()
        
        
    scheduele_soup = soup.find_all( "table", attrs={ "class": "linebox smart_table" } )
    scheduele_header = list()
    cnt = 0

    for i in scheduele_soup:
        for j in i.findAll("tr"):
            row_list = list()
            for k in j.findAll("td"):
                if cnt == 0:                

                    scheduele_header.append(k.get_text())
                    df_merge = pd.DataFrame( columns=scheduele_header ) 
                else:
                    row_list.append( k.get_text() )
            cnt+=1
            row_dict = dict( zip( scheduele_header, row_list ) )   
            row_df = pd.DataFrame().from_dict( row_dict, orient='index' ).transpose()
            df_merge = pd.concat([df_merge, row_df], sort= False)  

    df_merge = df_merge.dropna()

    for i in ["Home Team", "Visiting Team"]:
        df_merge[i] = df_merge[i].apply(lambda x:  str(x).replace(" (NEW)" , "")  )

    opponent_list = list(set(df_merge["Home Team"].to_list()))

    cur.execute( "delete from  events  where league  = 'Vancouver Metro Soccer League' ")
    conn.commit()

    for i in range( 0, len(df_merge) ):
        date = list()    
        location = df_merge["Field"].iloc[i]    
        if ( df_merge["Home Team"].iloc[i] == "Dinamo Anatolia" ):
            opponent_name = df_merge["Visiting Team"].iloc[i]
        if ( df_merge["Visiting Team"].iloc[i] == "Dinamo Anatolia" ):
            opponent_name = df_merge["Home Team"].iloc[i]
        
        [ date.append(str(df_merge["Date"].iloc[i]).split(" ")[1].split("/")[j])  for j in [2,1,0] ]
        hr =  int(str(df_merge["Date"].iloc[i]).split(" ")[2].split(":")[0])
        min = str(df_merge["Date"].iloc[i]).split(" ")[2].split(":")[1]
    
        if (min.__contains__("PM")):
            hr = hr +12
            if hr == 24:
                hr = 00
        
        min = min.replace("PM", "").replace("AM", "")
        
        date_str = str(date[0]) + "-" + str(date[2]) + "-" + str(date[1]) + " " + str(hr) + ":"+ str(min) + ":" + str(0)
        season = 2022
        league = "Vancouver Metro Soccer League"
        cur.execute( " insert into events ( event_location ,  opponent_name, event_date, season, league, league_season  ) \
        values (" + "'" + location + "'" + "," +  "'" + opponent_name +"'" + "," + "'" +  date_str + "'" + "," + "'" + str(2022) +"'" + "," + "'" + str(league)+ "'"  + "," + "'" + str(2022)  +"'"+ ")" ) 
        conn.commit()


    print("done")
    cur.close()
    conn.close()
        
    cnt = cnt+1
    print(cnt)
    print("database updated...")
      
    return "Flask heroku app"

if __name__ == "__main__":
    app.run()