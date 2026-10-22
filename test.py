import mariadb
import datetime
import pandas as pd
from mariadb.constants import INDICATOR
from datetime import timedelta
from dateutil.relativedelta import relativedelta
#import akshare as ak
import tushare as ts
#import baostock as bs
import time
import zone_node_class as znc
import trade as td
import copy as cp
import code
#获取浦发银行60000.SH的实时分钟数据
#df = pro.rt_min(ts_code='600000.SH,600008.SH', freq='5MIN')
#print(df)
table_struct = "trade_date date primary key, open float, high float, low float, close float, pct_ch float, vol float"
longin_mariadb_name = "root"
longin_mariadb_password = "123456"
db_name = "test1"
all_stock_list = [] #[("symbol","name"，"ts_code","idustre"行业,"list_date"上市日期)]
trade_date = []    #[("20260101",0 or 1)]
#stock_struct = [(code,trade_date,open,high,low,close,vol,pct_chg)]
stock_struct_list=[]
zone_node_dic_of_all_stock_list={} #{'symbol':zone_node}
support_and_pressure_dic = {}  #{'symbol'： 元组列表(close,date,zdnode_list)}   
dic_top_botton_of_zone_node = {} #顶点与底部{symbol：列表[({top:[zone_node]},{bottton:[zone_node]})]}
slash_value_dic_divide_group = {}        #{symbol:[top[],botton[(count,,stp,[])]]}  ((ct-index1)开始位,index1有多少个,stg（1，-1，0，CNT-1）,temp[])  
slash_node_dic={} #{symbol:[slash_node,slash_botton]}
init_true = 0
update_true = 1
init_start_date="20200101" #设制获取股的初始日期
update_name="date1.txt"
not_buy_plate="30,68,92,"

def sql_run(sql:str,data: list =0)->list:
    with mariadb.connect(f"mariadb://{longin_mariadb_name}:{longin_mariadb_password}@localhost") as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"use {db_name}")
            if data == 0:
                try:
                    cursor.execute(sql)
                except mariadb.DataError as e:
                    print("SQL_RUN错误",sql)
            else:
                try:
                    cursor.executemany(sql,data)
                except mariadb.DataError as e:
                        print("SQL_RUN错误",sql)
            temp_data = cursor.fetchall()
        conn.commit()
    return temp_data

def sql_run_void(sql:str,data: list =0):
   
    with mariadb.connect(f"mariadb://{longin_mariadb_name}:{longin_mariadb_password}@localhost") as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"use {db_name}")
            if data == 0:
                try:
                    cursor.execute(sql)
                except mariadb.DataError as e:
                    print("SQL_RUN错误",sql)
            else:
                try:
                    cursor.executemany(sql,data)
                except mariadb.DataError as e:
                        print("SQL_RUN错误",sql)
        conn.commit()   

#ts.set_token('ffdc91c27551a9e7ed1294e2e9132e40f5433d8c3622973f60b0b154')
ts_api = ts.pro_api('ffdc91c27551a9e7ed1294e2e9132e40f5433d8c3622973f60b0b154')
#### 登陆系统 ####
#lg = bs.login()
# 显示登陆返回信息
#print('login respond error_code:'+lg.error_code)
#print('login respond  error_msg:'+lg.error_msg)
def get_trade_date()->list:
    global trade_date
    start=(datetime.date.today()).strftime("%Y")+"0101"
    end=(datetime.date.today()).strftime("%Y") + "1231"     #+relativedelta(years=1))).strftime("%Y")+"1231"
    date=ts_api.query('trade_cal',start_date=start,end_date=end)[["cal_date","is_open"]].to_dict(orient="list")
    t0=list(date["cal_date"])
    t1=list(date["is_open"])
    index=0
    for vle in t0:
        trade_date.append((vle,t1[0]))
        index=index+1
    #print(trade_date)
    return trade_date
def get_all_stock_name():
    global all_stock_list
    data = ts_api.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    data= data[["symbol","name","ts_code","industry","list_date"]].to_dict(orient="list")
    t0=list(data["symbol"])
    t1=list(data["name"])
    t2=list(data["ts_code"])
    t3=list(data["industry"])
    t4=list(data["list_date"])
    index=0
    for vl in t0:
        all_stock_list.append((t0[index],t1[index],t2[index],t3[index],t4[index]))
        index=index+1
        #print(all_stock_list)
def init_stock_dbtable():
    global db_name
    global all_stock_list
    global table_struct
    with mariadb.connect(f"mariadb://{longin_mariadb_name}:{longin_mariadb_password}@localhost") as conn:
        with conn.cursor() as cursor:
            cursor.execute("show databases")
            name= cursor.fetchall()
            db_exist = 0
            for nm in name:
                if db_name == nm[0]:
                    db_exist = 1
                    break
            if db_exist==1:
                cursor.execute(f"use {db_name}")
            if db_exist==0:
                cursor.execute(f"create database {db_name}")
            cursor.execute(f"use {db_name}")
            for vle in all_stock_list:
                name_table = "a" + vle[0]
                cursor.execute(f"create table if not exists {name_table}({table_struct})")
                #print(name_table)
        conn.commit()
    pass
#STOCK_CODE="000006.SZ",START_DATE="20200101"....
def get_stock_data_start_end(stock_code,start,end)->dict:
    stock_data=[]
    data={}
    data_temp = ts_api.daily(ts_code=stock_code,start_date=start,end_date=end)
    temp = data_temp[["ts_code","trade_date","open","high","low","close","pct_chg","vol"]].to_dict(orient="list")
    t0 = list(temp["ts_code"])
    t1 = list(temp["trade_date"])
    t2 = list(temp["open"])
    t3 = list(temp["high"])
    t4 = list(temp["low"])
    t5 = list(temp["close"])
    t6 = list(temp["pct_chg"])
    t7 = list(temp["vol"])
    c = 0
    for tt in t1:
        if str(t6[c]) !="nan":
            stock_data.append((t0[c],t1[c],t2[c],t3[c],t4[c],t5[c],t6[c],t7[c]))
        c = c + 1
    #print(stock_data)
    while len(stock_code)>=9:
        temp = stock_code[0:9]
        code = temp[0:6]
        temp_list=[]
        #print(code)
        if len(stock_code)>9: 
            stock_code= stock_code[10:]
        elif len(stock_code) == 9:
            stock_code=""
        for tt in stock_data:
            if tt[0]==temp:
                temp_list.append((tt[1],tt[2],tt[3],tt[4],tt[5],tt[6],tt[7]))
        data[code]=temp_list
    return data

def init_all_table_data():
    global all_stock_list
    global init_start_date
    code=""
    for vle in all_stock_list:
        code =code + vle[2]+","
    init_year =  init_start_date[0:4]
    today_year = (datetime.date.today()).strftime("%Y")
    if int(today_year) < int(init_year):
        print("init_year too big")
        return 0
    if int(today_year) == int(init_year):
        if int(init_start_date[4:6]) > int(datetime.date.today().strftime("%m")):
            print("init_month too big")
            return 0
    if int(today_year) == int(init_year):
        if int(init_start_date[4:6]) == int(datetime.date.today().strftime("%m")):
            if int(init_start_date[6:8]) > int(datetime.date.today().strftime("%d")):
                print("init_date too big")
                return 0
    count_year=int(today_year)-int(init_year)+1
    with mariadb.connect(f"mariadb://{longin_mariadb_name}:{longin_mariadb_password}@localhost") as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"use {db_name}")
            count_1=0
            start_date=""
            end_date=""
            while count_1 < count_year:
                if count_year==1:
                    start_date =  init_start_date
                    end_date= (datetime.date.today()).strftime("%Y%m%d")
                if count_year>2:
                    if count_1==0:
                        start_date=init_start_date
                        end_date=init_start_date[0:4]+"1231"
                    if count_1 >= 1:
                        start_date = str(int(end_date[0:4]) + 1)+"0101"
                        if count_1 != (count_year-1):
                            end_date = start_date[0:4]+"1231"
                        else:
                            end_date=(datetime.date.today()).strftime("%Y%m%d")
                count_2=0
                len_1 = (len(code))/10
                ts_code=""
                code_1 =code
                #print(start_date,end_date)
                while count_2 < len_1:
                    if (count_2+20) < len_1:
                        count =  20*10
                        ts_code=code_1[0:count]
                        #print(ts_code)
                        code_1 = code_1[count:]
                        #print(code_1)
                    else:
                        ts_code=code_1
                        #print(ts_code)
                    temp_dict_data = get_stock_data_start_end(ts_code,start_date,end_date)
                    for ky,vl in temp_dict_data.items():
                        cursor.execute(f"create table if not exists a{ky}({table_struct})")
                        sql = f"insert into a{ky} (trade_date,open,high,low,close,pct_ch,vol) values (%s,%s,%s,%s,%s,%s,%s)"
                        print(sql)
                        cursor.executemany(sql,vl)
                    conn.commit()
                    count_2 = count_2 + 20
                count_1 = count_1 +1
                #print(count_1)
            with open(f"{update_name}","a+",encoding='utf-8') as ff:
                ff.write(f"\n{end_date}")
        conn.commit()

def update_all_stock_data():
    global init_start_date
    today =(datetime.date.today()).strftime("%Y%m%d")
    data_cru=''
    with open(f"{update_name}","a+",encoding='utf-8') as ff:
        ff.seek(0)
        temp = ff.readline()
        while temp !="":
            if temp !="":
                data_cru=temp
            temp = ff.readline()
        data_cru = datetime.datetime.strptime(data_cru,"%Y%m%d")
        data_cru =(data_cru + datetime.timedelta(days=1)).strftime("%Y%m%d")
    if int(today[0:4]) < int(data_cru[0:4]):
        print("UPDATE_ALL_STOCK_DATA year不需要更新")
        return 0
    if (int(today[4:6]) < int(data_cru[4:6])) and (int(today[0:4]) == int(data_cru[0:4])) :
        print("UPDATE_ALL_STOCK_DATA mauth不需要更新")
        return 0
    if (int(today[6:8]) < int(data_cru[6:8])) and (int(today[4:6]) < int(data_cru[4:6])) and (int(today[0:4]) == int(data_cru[0:4])):
        print("UPDATE_ALL_STOCK_DATA date不需要更新")
        return 0
    init_start_date=data_cru
    init_all_table_data()
    print("UPDATE_ALL_STOCK_DATA更新完成")
    print((data_cru, today))
    return 0
#tscode="000001"start="20201001" end="230101"
def get_data_start_end_from_db_table(tscode,start,end)->list:
    global db_name
    tscode= 'a'+ tscode
    data=[]
    with mariadb.connect(f"mariadb://{longin_mariadb_name}:{longin_mariadb_password}@localhost") as conn:
        with conn.cursor() as cursor:
                cursor.execute(f"use {db_name}")
                cursor.execute(f"show tables")
                all_stock_table_name = cursor.fetchall()
                for val in all_stock_table_name:
                    if tscode == val[0]:
                        cursor.execute(f"select * from {tscode} where trade_date >= {start} AND trade_date <= {end}" )
                        data=cursor.fetchall()
        conn.commit()
    return data
#构建区间链表stock_code="000001",start_date="20250101",end_date="20260101"
def zone_list(stock_code:str,start_date,end_date)->znc.ZoneNode:
    with mariadb.connect(f"mariadb://{longin_mariadb_name}:{longin_mariadb_password}@localhost") as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"use {db_name}")
            #cursor.execute(f"show tables")
            sql = "select trade_date,open,high,low,close,pct_ch,vol from a" + f"{stock_code} where trade_date >= {start_date} AND trade_date <= {end_date}" + " order by trade_date asc"
            cursor.execute(sql)
            data_stock_code = cursor.fetchall()
            #print(data_stock_code)
        conn.commit()
    if len(data_stock_code) < 1:
        return None
    head = znc.ZoneNode()
    curr_node = head
    next_node = head
    head.date = data_stock_code[0][0]
    head.close = data_stock_code[0][4]
    head.open = data_stock_code[0][1]
    head.high = data_stock_code[0][2]
    head.low = data_stock_code[0][3]
    head.pct_ch=data_stock_code[0][5]
    head.vol=data_stock_code[0][6]
    flage_up = 0
    flage_down = 0
    flage_turn = 0
    up_top_flage = 0
    curr_node_date = 0
    node_index=0
    temp_i = 0
    temp_save_vl =0
    for i in range(len(data_stock_code)-1):
        temp_node_close = data_stock_code[i+1][4]
        temp_node_date = i+1
        curr_node_close = curr_node.close
        if curr_node_close < temp_node_close:
            if((temp_node_close - curr_node_close)/curr_node_close) > 0.05:
                    if flage_up == 0 :
                        node_index = 0
                        flage_up = 1
                        flage_down = 0
                        flage_turn = 1
                        up_top_flage = 1
                        curr_node.top_flage = 0
                        ##以下三个变量用于大于百分三的
                        node_index = 0
                        temp_save_vl = 0
                        temp_i = 0
            elif((temp_node_close - curr_node_close)/curr_node_close) >0.03:
                if flage_up == 0:
                    if temp_save_vl < temp_node_close:
                        temp_save_vl = temp_node_close
                        node_index = i
            if node_index != 0:
                if temp_node_date - curr_node_date > 5:
                    if flage_up == 0:
                        flage_up = 1
                        flage_down = 0
                        flage_turn = 1
                        up_top_flage = 1
                        curr_node.top_flage =0
                        temp_i = i
        if curr_node_close > temp_node_close:
            if((curr_node_close - temp_node_close)/curr_node_close) > 0.05:
                    if flage_down == 0 :
                        node_index = 0
                        flage_up = 0
                        flage_down = 1
                        flage_turn = 1
                        up_top_flage = 0
                        curr_node.top_flage =1
                        node_index=0
                        temp_save_vl=0
                        temp_i = 0
            elif((curr_node_close - temp_node_close)/curr_node_close) > 0.03:
                if flage_down==0:
                    if temp_save_vl > temp_node_close:
                        temp_save_vl = temp_node_close
                        node_index = i
            if node_index != 0:
                if temp_node_date - curr_node_date > 5:
                    if flage_up == 0:
                        flage_up = 1
                        flage_down = 0
                        flage_turn = 1
                        up_top_flage = 1
                        curr_node.top_flage =0
                        temp_i = i
        if flage_turn == 1 :
            if node_index != 0:
                i = node_index
            flage_turn = 0
            next_node= znc.ZoneNode()
            next_node.date = data_stock_code[i+1][0]
            next_node.open = data_stock_code[i+1][1]
            next_node.high = data_stock_code[i+1][2]
            next_node.low = data_stock_code[i+1][3]
            next_node.close = data_stock_code[i+1][4]
            next_node.pct_ch = data_stock_code[i+1][5]
            next_node.vol = data_stock_code[i+1][6]
            next_node.top_flage = up_top_flage
            curr_node.down_node = next_node
            next_node.up_node = curr_node
            curr_node = next_node
            curr_node_date = i
            if node_index !=0:
                i = temp_i
                node_index = 0
                temp_save_vl =0
                temp_i=0
            continue
        if flage_up == 1:
            if curr_node.close < temp_node_close:
                curr_node.close = temp_node_close
                curr_node.date = data_stock_code[i+1][0]
                curr_node.open = data_stock_code[i+1][1]
                curr_node.high = data_stock_code[i+1][2]
                curr_node.low = data_stock_code[i+1][3]
                curr_node.pct_ch = data_stock_code[i+1][5]
                curr_node.vol = data_stock_code[i+1][6]
                curr_node_date = i
                node_index = 0
        if flage_down == 1:
            if curr_node.close > temp_node_close:
                curr_node.close = temp_node_close
                curr_node.date = data_stock_code[i+1][0]
                curr_node.open = data_stock_code[i+1][1]
                curr_node.high = data_stock_code[i+1][2]
                curr_node.low = data_stock_code[i+1][3]
                curr_node.pct_ch = data_stock_code[i+1][5]
                curr_node.vol = data_stock_code[i+1][6]
                curr_node_date = i
                node_index = 0
    return head        
def optimize_zone_node(node:znc.ZoneNode)->znc.ZoneNode:
    head = node
    cur = next1 = node
    if node != None:
        if node.top_flage ==1:
            if node.down_node != None:
                next1 = cur = node.down_node
            else:
                return head    
        if node.top_flage == 0:
            if node.down_node ==None:
                return head
            if node.down_node != None:
                cur = node.down_node
                if cur.down_node == None:
                    return head
                if cur.down_node !=None:
                    cur = cur.down_node    
    while cur != None:
        next1= cur.down_node
        if next1 != None:
            day1 = (next1.date - cur.date).days
            #step = abs(next1.close - curr.close)/curr.close
            if day1 <=4 :
                temp = next1.down_node
                if temp != None:
                    if cur.close > temp.close:
                        temp.up_node = cur.up_node
                        nd = cur.up_node
                        nd.down_node= temp
                        cur = temp

                    if cur.close <= temp.close:
                        cur.down_node = temp.down_node
                        if temp.down_node !=None:
                            temp.down_node.up_node = cur
                        if temp.down_node == None:
                            return head
                if temp == None:
                    cur = temp
            if day1 > 4:
                cur = next1.down_node
        if next1 == None:
            return head
    return head
def zone_list_in_list(code:list,start_date,end_date)->dict:
    temp_dict = dict()
    for i in range(len(code)):
        temp_dict[code[i]] = optimize_zone_node(zone_list(code[i],start_date,end_date))
    return temp_dict
def init_zone_list_of_all_stock__list(year_count=4):
    global zone_node_dic_of_all_stock_list   #{'symbol':zone_node}
    global all_stock_list  #all_stock_list[("symbol","name"，"ts_code")]
    end_date = (datetime.date.today()).strftime("%Y%m%d")
    start_date= ((datetime.datetime.strptime(end_date,"%Y%m%d")) - relativedelta(years=year_count)).strftime("%Y%m%d")
    temp_code=[]
    for i in all_stock_list:
        temp_code.append(i[0])
    zone_node_dic_of_all_stock_list = zone_list_in_list(temp_code,start_date,end_date)

def connect_same_zone_node_of_close(node:znc.ZoneNode)->znc.ZoneNode: 
    zone_node = node
    while node is not None:    
        if node.same_left_node is  None:  
            temp_node1=node
            temp_node2=node.down_node 
            while temp_node2 is not None:
                flage_same = 0
                if node.close > temp_node2.close:
                    if (node.close - temp_node2.close)/node.close < 0.01:
                        flage_same = 1
                if node.close < temp_node2.close:
                    if (temp_node2.close - node.close)/node.close < 0.01:
                        flage_same = 1
                if node.close == temp_node2.close:
                    flage_same = 1
                if flage_same == 1:
                    temp_node1.same_right_node = temp_node2
                    temp_node2.same_left_node =  temp_node1
                    temp_node1 = temp_node2
                temp_node2 = temp_node2.down_node
        node = node.down_node
    return zone_node
def connect_same_close_of_all_zone_node():
    for key,val in zone_node_dic_of_all_stock_list.items():
        if val is not None:
            connect_same_zone_node_of_close(val)
def support_and_pressure_of_zone_node():
    global zone_node_dic_of_all_stock_list
    global support_and_pressure_dic
    connect_same_close_of_all_zone_node()
    for key,node in zone_node_dic_of_all_stock_list.items():
        temp_list =[]
        while node is not None:
            if node.same_left_node is None:
                temp_list.append((node.close,node.date,node))
            node = node.down_node
        temp_list.sort()
        support_and_pressure_dic[key] = temp_list
def set_update():
    global update_true
    trade_date=get_trade_date()
    temp = str(datetime.datetime.now().strftime("%Y%m%d"))
    time = int (datetime.datetime.now().strftime("%H"))
    with open(f"{update_name}","a+",encoding="utf-8") as f:
        f.seek(0)
        line = f.readlines()
        if len(line) == 0:
            update_true = 1
        if (len(line)) > 0 :
            last_line = line[-1].strip()
            if last_line != temp:
                update_true = 1 
    for vol in trade_date:
        #print(temp)
        if temp == str(vol[0]):
            if vol[1] == 1:
                if time > 16:
                    update_true = 1
                #print(temp)
def get_max_and_min_for_zone_node(node:znc.ZoneNode)->tuple:
    next_node = node.down_node
    max_node =  node
    min_node =  node
    curr =  node
    while next_node != None:
        curr = next_node
        next_node = next_node.down_node
        if max_node.close < curr.close:
            max_node = curr
            continue
        if min_node.close > curr.close:
            min_node = curr
            continue
        temp = (max_node,min_node,curr)
    return temp
def set_dic_top_botton_of_zone_node():
    global zone_node_dic_of_all_stock_list
    global dic_top_botton_of_zone_node
    for ky,val in zone_node_dic_of_all_stock_list.items():
        lst_t=[]
        lst_b=[]
        while val != None:
            if val.top_flage == 1:
                lst_t.append(val)
            if val.top_flage == 0:
                lst_b.append(val)
            val = val.down_node
        ls1=[]
        cnt = 0
        for vl in lst_t:
            if cnt == 0:
                cnt = vl.close
                ls1.append(vl)
            if cnt != 0:
                if abs(vl.close-cnt)/cnt > 0.05:
                    ls1.append(vl)
                    cnt=vl.close
        cnt = 0
        ls2=[]
        for vl in lst_b:
            if cnt == 0:
                cnt = vl.close
                ls2.append(vl)
            if cnt != 0:
                if abs(vl.close-cnt)/cnt > 0.05:
                    ls2.append(vl)
                    cnt=vl.close        
        dic_top_botton_of_zone_node[ky] = [({"top":ls1},{"botton":ls2})]
#点（znc.ZoneNode DATE表示X，close表示y）到斜线的距离
def distance_to_slash(node1:znc.ZoneNode, node2:znc.ZoneNode, node3:znc.ZoneNode)->float:
    a1=((node1.date).day,node1.close)
    b2=((node2.date-node1.date).days + node1.date.day,node2.close)
    c3=((node3.date-node1.date).days + node1.date.day,node3.close)
    a = b2[1]-a1[1]
    b = a1[0]-b2[0]
    c = b2[0]*a1[1] - a1[0]*b2[1]
    d = abs(a*c3[0]+b*c3[1]+c) / ((a**2+b**2)**0.5)
    #print((a1,b2,c3))
    return d

#两点的斜率
def slash(node1:znc.ZoneNode,node2:znc.ZoneNode)->float:
    a1=((node1.date).day,node1.close)
    b2=((node2.date-node1.date).days + node1.date.day,node2.close)
    a=b2[1]-a1[1]
    b=a1[0]-b2[0]
    #print((a,b))
    return a/b
def  slash_divide_into_group(ls:list)->list: 
    ct = 0
    ls1=[]
    while ct < (len(ls)-1):
        ls1.append(slash(ls[ct],ls[ct+1]))
        ct =ct +1
    #print(ls1)
    ls3=[]
    ct = index1 =0
    vl1=vl2=0
    stg=0  #stg=1,-1,0 ，2，len(ls1)-1
    while ct < len(ls1):
        if len(ls1)==1 :
            vl1=ls1[ct]
            return[(ct,1,2,[vl1])]
        if (len(ls1)-ct) >= 2:
            vl1=ls1[ct]
            vl2=ls1[ct+1]
            if (vl1>0 and vl2>0) or (vl1<0 and vl2<0):
                if vl1>0 and vl2>0:
                    stg = 1
                if vl1<0 and vl2<0:
                    stg = -1
            if (vl1<0 and vl2>0) or (vl1>0 and vl2 <0):
                stg=0
        if (len(ls1)-ct)==1:
            ls3.append((ct,1,ct,[ls1[ct]]))
            return ls3

        if stg==-1:
            temp=[]
            index1 = 0
            while ct<len(ls1):
                if ls1[ct]<0:
                    temp.append(ls1[ct])
                    index1 = index1+1
                    ct= ct+1
                else:
                    break
            ls3.append(((ct-index1),index1,stg,temp))
        if stg==1:
            temp=[]
            index1 = 0
            while ct<len(ls1):
                if ls1[ct]>0:
                    temp.append(ls1[ct])
                    index1 = index1+1
                    ct= ct+1
                else:
                    break
            ls3.append(((ct-index1),index1,stg,temp))
        if stg==0:
            temp=[]
            index1 = 0
            while ct<(len(ls1)-1):
                temp1=temp2=0
                if ls1[ct] > 0:
                    temp1=1
                else:
                    temp1=-1
                if ls1[ct+1]>0:
                    temp2=1
                else:
                    temp2 = -1
                if (temp1+temp2)==0:
                    temp.append(ls1[ct])
                    index1 = index1+1
                    ct= ct+1
                else:
                    break
            ls3.append(((ct-index1),index1,stg,temp))
    return ls3
def set_slash_value_dic_divide_group():
    global  dic_top_botton_of_zone_node
    global   slash_value_dic_divide_group
    cnt=0
    for key, vl in dic_top_botton_of_zone_node.items():
        vl_t= vl[0][0]["top"]
        vl_b=vl[0][1]["botton"]
        cnt=cnt+1
        vl_t =  slash_divide_into_group(vl_t)
        vl_b =  slash_divide_into_group(vl_b)
        #print(("slash-------",cnt))
        slash_value_dic_divide_group[key]=[vl_t,vl_b]
#ls is list with slash_node
def sort_structure_node_with_slash_group(ls:znc.slash_node)->list:
    max_node=0
    max_val=0
    sort_list=[]
    while ls !=None:
        in_ls=ls
        max_val=0
        while in_ls!=None:
            curr_val=in_ls.top_vlue.close
            if max_val < curr_val:
                max_val = curr_val
                max_node=in_ls
            if in_ls.slash_node_next !=None:
                in_ls=in_ls.slash_node_next
            else:
                break
        if ls.slash_node_next == None and ls.slash_node_up == None:
            ls = None
        max_node_next = max_node.slash_node_next
        max_node_up = max_node.slash_node_up
        if max_node_up !=None:
            max_node_up.slash_node_next=max_node_next
        else:
            ls=max_node_next
            if max_node_next!=None:
                max_node_next.slash_node_up=None
        if max_node_next !=None:
            max_node_next.slash_node_up=max_node_up
        else:
            if  max_node_up!=None:
                max_node_up.slash_node_next=None
        #print(("aaa",max_val))
        sort_list.append(max_node)
    return sort_list
#top[(count,,,[])]
def structure_node_with_slash_group(ls:list)->znc.slash_node:
    global dic_top_botton_of_zone_node
    if len(ls)==1:
        node = znc.slash_node()
        node.slash_node_next=None
        node.slash_node_up= None
        node.left_zone=ls[0]
        node.right_zone=None
        node.top_index = ls[0][0]+ls[0][1]
        return node
    if len(ls)==0:
        return None
    cnt=0
    head=None
    while cnt<(len(ls)-1):
        node = znc.slash_node()
        node.slash_node_next=None
        node.slash_node_up= None
        if cnt < len(ls):
            node.right_zone=ls[cnt+1]
            node.top_index=ls[cnt+1][0]
            if head==None:
                node.left_zone=ls[cnt]
                head=cur=node
                cnt=cnt+1
                continue
            if head!=None:
                node.left_zone=ls[cnt]
                cur.slash_node_next=node
                node.slash_node_up=cur
                cur=node
        cnt=cnt+1
    return head
def all_top_botton_with_slash_node():
    global slash_node_dic
    global dic_top_botton_of_zone_node
    global slash_value_dic_divide_group
    dic=slash_value_dic_divide_group
    for key1,value in dic.items():
        top=value[0]    #value[[],[]]
        botton=value[1]
        top=structure_node_with_slash_group(top)
        botton=structure_node_with_slash_group(botton)
        ls1=top
        while ls1!=None:
            index=ls1.top_index
            ls1.top_vlue=dic_top_botton_of_zone_node[key1][0][0]["top"][index]
            ls1 = ls1.slash_node_next
        ls2=botton
        while ls2!=None:
            index=ls2.top_index
            ls2.top_vlue=dic_top_botton_of_zone_node[key1][0][1]["botton"][index]
            ls2 = ls2.slash_node_next
        slash_node_dic[key1]=[ls1,ls2]
#在lash_value_dic_divide_group变量中查找最后一组COUNT=1的stock 
def find_count_for_two_slash_value()->list:
    global slash_value_dic_divide_group
    id=[]
    cnt=0
    for key,vl in slash_value_dic_divide_group.items():
        top=vl[0]
        botton=vl[1]
        len_t=len(top)
        len_b=len(botton)
        #cnt=cnt+1
        #print(botton)
        """
        if len_t>0:
            if top[len_t-1][1]<=1:
                id.append(key)
                continue
        """
        
        if len_b>0:
            if botton[len_b-1][1]==1:
                if botton[len_b-1][3][0]<0:
                    id.append(key)
                    #print(botton[len_b-1])
                    continue
        
    return id

def delete_not_buy_plate(stock)->list:
    global not_buy_plate
    count = len(not_buy_plate)/3
    temp=not_buy_plate
    data=[]
    while count>0:
        count=count-1
        name=temp[0:3][0:2]
        temp=temp[3:]
        for vla in stock:
            temp1=vla[0:2]
            if name != temp1:
                data.append(vla)
        stock=data
        data=[]
    return stock
#获取DT过去ct天的平均交易量
#STOCK_CODE代码，指定DT日期开始CT日的平均交易量。
#dt="20260101" fd= 0 or 1
def get_arerage_data(stock_code:str,dt:str,cnt:int,fd:int=0):
    fild_name="vol"
    if fd == 0:
        fild_name = "vol"
    if fd == 1:
        fild_name = "close"
    with mariadb.connect(f"mariadb://{longin_mariadb_name}:{longin_mariadb_password}@localhost") as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"use {db_name}")
            sql = "select trade_date," + f" {fild_name}" + " from a" + f"{stock_code}" + " where trade_date <= " + f"{dt}" + " order by trade_date desc"
            data_stock_code = sql_run(sql)
    if len(data_stock_code) < cnt:
        cnt = len(data_stock_code)
    ct = 0
    nu = 0
    while ct < cnt:
        nu = nu +data_stock_code[ct][1]
        ct = ct + 1
    return nu/cnt
#获取指定STOCK_CODER 的K线上中下的比利
def get_appiont_date_umb(stock_code:str,dt:str)->tuple:
    with mariadb.connect(f"mariadb://{longin_mariadb_name}:{longin_mariadb_password}@localhost") as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"use {db_name}")
            cursor.execute(f"show tables")
            sql = "select * from a" + f"{stock_code}" + " where trade_date = " + f"{dt}"
            data_stock_code = sql_run(sql)
    print(data_stock_code)
    zn = data_stock_code[0][2] - data_stock_code[0][3]
    md = abs(data_stock_code[0][1] - data_stock_code[0][4])
    #一字
    if zn==0:
        return (1,1,1)
    #收红
    if data_stock_code[0][1] < data_stock_code[0][4]:
        up1 = data_stock_code[0][2] - data_stock_code[0][4]
        down = data_stock_code[0][1] - data_stock_code[0][3]
    #收绿
    if data_stock_code[0][1] > data_stock_code[0][4]:
        up1 = data_stock_code[0][2] - data_stock_code[0][1]
        down = data_stock_code[0][4] - data_stock_code[0][3]
    return (up1/zn,md/zn,down/zn)
#############################################
###############################################
#获取指定STOCK_COde的某日的数据
def get_appiont_date_data(stock_code:str,dt:str):
    with mariadb.connect(f"mariadb://{longin_mariadb_name}:{longin_mariadb_password}@localhost") as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"use {db_name}")
            cursor.execute(f"show tables")
            sql = "select * from a" + f"{stock_code}" + " where trade_date = " + f"{dt}"
            data_stock_code = sql_run(sql)
    return data_stock_code

#获取指定股票的指定天数的平均交易
def get_average_vol(code,days):
    everager_data = []
    sql="select * from a"+code
    get_data=sql_run(sql)
    #print(get_data)
    if len(get_data) < days:
        count=0
        j=0
        while j < len(get_data):
            count= count + get_data[j][6]
            j=j+1
        j=j-1
        temp=(get_data[j][0],count/j)
        everager_data.append(temp)
        return everager_data
    i=0
    while i < (len(get_data)-days+1):
        j = 0
        count = 0
        while j < days:
                if i+j < len(get_data):
                    count = count + get_data[i+j][6]
                    j = j + 1
                else:
                    break
        j=j-1
        temp = (get_data[i+j][0],count/days)
        i=i+1
        everager_data.append(temp)
    print(everager_data)
    return everager_data

#获取指定股票的指定天数的平均数据
def get_average_data(code,days):
    everager_data = []
    sql="select * from a"+code
    get_data=sql_run(sql)
    #print(get_data)
    if len(get_data) < days:
        count=0
        j=0
        while j < len(get_data):
            count= count + get_data[j][4]
            j=j+1
        j=j-1
        temp=(get_data[j][0],count/j)
        everager_data.append(temp)
        return everager_data
    i=0
    while i < (len(get_data)-days+1):
        j = 0
        count = 0
        while j < days:
                if i+j < len(get_data):
                    count = count + get_data[i+j][4]
                    j = j + 1
                else:
                    break
        j=j-1
        temp = (get_data[i+j][0],count/days)
        i=i+1
        everager_data.append(temp)
    return everager_data


#return stock id list
def select_stockA()->list:
    

    pass
def select_stockB()->str:
    pass

def main():
    set_update()
    print("run get_all_stock_name------->")
    get_all_stock_name()
    if init_true == 1:
        print("run init_stock_dbtable------->")
        init_stock_dbtable()
        print("run init_all_table_data-------->")
        init_all_table_data()
    if update_true == 1:
        print("run update_all_stock_data-------->")
        update_all_stock_data()
    print("run init_zone_list_of_all_stock_list--------->")
    init_zone_list_of_all_stock__list()
    print("run support_and_pressure_of_zone_node----------->")
    support_and_pressure_of_zone_node()
    print("run set_dic_top_botton_of_zone_node")
    set_dic_top_botton_of_zone_node()
    print("run  set_slash_value_dic_divide_group")
    set_slash_value_dic_divide_group()
    print("run  all_top_botton_with_slash_node")
    all_top_botton_with_slash_node()
    ##trade.py
    print("run td.login-------->")  
    #td.login(

#get_all_stock_name()
#init_stock_dbtable()
#init_all_table_data()
#print((2024%3))
#   
#pdate_all_stock_data()
"""
with open("date1.txt","r",encoding="utf-8") as ff:
    ff.seek(0,2)
    last_line=ff.readline().decode("utf-8").strip()
    print(last_line)
    """
#print(get_stock_data_start_end("000001.SZ,000002.SZ,","20200101","20261008"))

main()
print(len(delete_not_buy_plate(find_count_for_two_slash_value())))
#get_data_start_end_from_db_table("000001","20231001","20231012")
"""
#get_average_vol("600584",1)
print(find_count_for_two_slash_value())
"""
"""
temp2=temp1 = optimize_zone_node(zone_list("600171","20241228","20260201"))
ls=[]
while temp1!=None:
    if temp1.top_flage == 0:
        ls.append(temp1)
    temp1 = temp1.down_node 
ls1=[]
cnt = 0
for vl in ls:
    if cnt == 0:
        cnt = vl.close
        ls1.append(vl)
    if cnt != 0:
        if abs(vl.close-cnt)/cnt > 0.05:
            ls1.append(vl)
            cnt=vl.close
print(ls1)
ls2=slash_divide_into_group(ls1)
print("ssssssssssssssssss")
print(ls2)
head=ls=ls3=structure_node_with_slash_group(ls2)
while ls3!=None:
    index=ls3.top_index
    ls3.top_vlue=ls1[index]
    ls3 = ls3.slash_node_next

while ls!=None:
    print((ls.top_index,ls.top_vlue))
    print((ls.left_zone,ls.right_zone))
    ls = ls.slash_node_next
ls=head
while ls!=None:
    print((ls.top_vlue.close,ls.top_vlue.date))
    ls=ls.slash_node_next
"""