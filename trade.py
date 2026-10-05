import win32api
import win32gui
import time
def query_untrade_stock():
    global windows_handle
    
    list_temp=[]
    dic_temp ={"证券代码": 0, "股票名": 0, "委托价格": 0, "撤单数量":0}
    win32gui.ShowWindow(windows_handle,win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_handle,win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(windows_handle)
    time.sleep(2)
    move_window_to_center(windows_handle)
    win32gui.SetWindowPos(windows_handle,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    win32api.keybd_event(win32con.VK_F3,0,0,0)
    win32api.keybd_event(win32con.VK_F3,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(2)
    windows_list = enum_all_child(windows_handle)
    #print(windows_list)
    windows_list = find_windows_classname(windows_list, "CVirtualGridCtrl")
    left,top,right,bottom=win32gui.GetWindowRect(windows_list[0][1])
    x = left+ (right-left) // 2
    y = top + 22
    while True:
        y = y + 22
        win32api.SetCursorPos((x,y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
        time.sleep(3)
        proces_windows_handle=get_windows_by_pid(proces_id[0])
        if proces_windows_handle[0] == windows_handle:
            break
        curr_windows_handle =enum_all_child(proces_windows_handle[0])
        #print(curr_windows_handle)
        butt_list = find_button(curr_windows_handle)
        static_list = find_windows_classname(curr_windows_handle,"Static")
        n = len(static_list)
        name = get_control_text(static_list[(n-3)][1])
        prices = get_control_text(static_list[(n-2)][1])
        count = get_control_text(static_list[(n-1)][1])
        dic_temp["证券代码"]= (name.replace("证券代码：",""))[:6]
        dic_temp["股票名"] = (((name.replace("证券代码：",""))[6:])[1:])[:-1]
        dic_temp["委托价格"]=(prices.replace("委托价格：","")).strip()
        dic_temp["撤单数量"] = (count.replace("撤单数量：","")).replace("（以实际撤单数量为准）","").strip()
        list_temp.append(dic_temp.copy())
        left,top,right,bottom=win32gui.GetWindowRect(butt_list[1][1])
        x1=(left+right)//2
        y1=(top+bottom)//2
        win32api.SetCursorPos((x1,y1))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
        #time.sleep(3)
        #print(list_temp)
    return list_temp

def cancel_trade_stock(id:str):
    untrad_stock = query_untrade_stock()
    win32gui.ShowWindow(windows_handle,win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_handle,win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(windows_handle)
    time.sleep(2)
    move_window_to_center(windows_handle)
    win32gui.SetWindowPos(windows_handle,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    win32api.keybd_event(win32con.VK_F3,0,0,0)
    win32api.keybd_event(win32con.VK_F3,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(2)
    windows_list = enum_all_child(windows_handle)
    windows_list = find_windows_classname(windows_list, "CVirtualGridCtrl")
    left,top,right,bottom=win32gui.GetWindowRect(windows_list[0][1])
    x = left+ (right-left) // 2
    y = top + 22
    c = 1
    for stock in untrad_stock:
        if stock["证券代码"] == id:
            win32api.SetCursorPos((x,(y+c*22)))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
            time.sleep(3)
            proces_windows_handle=get_windows_by_pid(proces_id[0])
            curr_windows_handle =enum_all_child(proces_windows_handle[0])
            #print(curr_windows_handle)
            butt_list = find_button(curr_windows_handle)
            left,top,right,bottom=win32gui.GetWindowRect(butt_list[0][1])
            x1=(left+right)//2
            y1=(top+bottom)//2
            win32api.SetCursorPos((x1,y1))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
        c = c+1

def query_account_information():
    global windows_handle
    win32gui.ShowWindow(windows_handle,win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_handle,win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(windows_handle)
    time.sleep(2)
    move_window_to_center(windows_handle)
    win32gui.SetWindowPos(windows_handle,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    win32api.keybd_event(win32con.VK_F4,0,0,0)
    win32api.keybd_event(win32con.VK_F4,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(10)
    windows_list = enum_all_child(windows_handle)
    windows_list = enum_all_child(windows_list[6][1])
    account_information["资金余额"] = float(windows_list[4][2])
    account_information["冻结金额"] = float(windows_list[5][2])
    account_information["可用金额"] = float(windows_list[6][2])
    account_information["可取金额"] = float(windows_list[10][2])
    account_information["股票市值"] = float(windows_list[11][2])
    account_information["总 资 产"] = float(windows_list[12][2])
    account_information["持仓盈亏"]  = float(windows_list[14][2])
    #account_information["当日盈亏"]  = float(windows_list[16][2])
    #ccount_information["当日盈亏比"] = float(windows_list[18][2][:-1])
    #print(account_information)
    pass


def buy_sell_input_trade(stock_id:str, quantity:int, price:float):
    windows_list = enum_all_child(windows_handle)
    windows_list = enum_all_child(windows_list[6][1])
    edit_list = find_edit_input(windows_list)
    left,top,right,bottom=win32gui.GetWindowRect(edit_list[0][1])
    x=(left+right)//2
    y=(top+bottom)//2
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(0.5)
    send_str(stock_id)
    time.sleep(0.5)
    left,top,right,bottom=win32gui.GetWindowRect(edit_list[1][1])
    x=(left+right)//2
    y=(top+bottom)//2
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(0.5)
    send_str(price)
    left,top,right,bottom=win32gui.GetWindowRect(edit_list[2][1])
    x=(left+right)//2
    y=(top+bottom)//2
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(0.5)
    quantity = str(quantity)
    send_str(quantity)
    button =  find_button(windows_list)
    left,top,right,bottom=win32gui.GetWindowRect(button[0][1])
    x=(left+right)//2
    y=(top+bottom)//2
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(1)
    proces_windows_handle=get_windows_by_pid(proces_id[0])
    butt_list = find_button(enum_all_child(proces_windows_handle[0])) 
    left,top,right,bottom=win32gui.GetWindowRect(butt_list[0][1])
    x=(left+right)//2
    y=(top+bottom)//2
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(1)   

def buy_stock(stock_id:str, quantity:int, price:float):
    global windows_handle
    win32gui.ShowWindow(windows_handle,win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_handle,win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(windows_handle)  
    time.sleep(2)
    move_window_to_center(windows_handle)
    win32gui.SetWindowPos(windows_handle,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    win32api.keybd_event(win32con.VK_F1,0,0,0)
    win32api.keybd_event(win32con.VK_F1,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(2)
    buy_sell_input_trade(stock_id,quantity,price)
    
def sell_stock(stock_id:str, quantity:int, price:float):
    global windows_handle
    top_handle = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(windows_handle,win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_handle,win32con.SW_RESTORE)
    if top_handle != windows_handle:
        win32gui.SetForegroundWindow(windows_handle)
    time.sleep(2)
    move_window_to_center(windows_handle)
    win32gui.SetWindowPos(windows_handle,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    time.sleep(0.5)
    win32api.keybd_event(win32con.VK_F2,0,0,0)
    time.sleep(0.05)
    win32api.keybd_event(win32con.VK_F2,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(2)
    buy_sell_input_trade(stock_id, quantity, price)



def login():
    global windows_handle
    if not is_process_running(proces_name):
        handl= win32process.CreateProcess(start_app,'',None,None,0,win32process.CREATE_NO_WINDOW,None,None,win32process.STARTUPINFO())
        proces_id.append(handl[2])
        #print(proces_id)
    time.sleep(5)
    w_handle = get_windows_by_pid(proces_id[0])
    title = win32gui.GetWindowText(w_handle[0])
    if title == "网上股票交易系统5.0":
        windows_handle = w_handle[0]
        return True
    w_handle = enum_all_child(w_handle[0])
    select_simulate_trade(w_handle)
    query_account_information()
    return True
    """"
    w_handle= win32gui.FindWindow(None,"登录到全部行情主站")
    #print(w_handle)
    child_windows = []
    if w_handle:
        child_windows = enum_all_child(w_handle)
    if not w_handle:
        return 0
    #print(child_windows)
    edit_hwnds = find_edit_input(child_windows)
    #print(edit_hwnds)
    input_to_edit(edit_hwnds[0][1],name)
    time.sleep(1)
    left,top,right,bottom=win32gui.GetWindowRect(edit_hwnds[1][1])
    x=(left+right)//2
    y=(top+bottom)//2
    #print(x,y)
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP,0,0,0,0)
    time.sleep(1)
    input_to_edit(edit_hwnds[1][1],passwd)
    time.sleep(1)
    login_windows_whandle = find_login_title(child_windows)
    #print(login_windows_whandle)
    win32api.SendMessage(login_windows_whandle[0][1],win32con.BM_CLICK,0,None)
    #win32api.SendMessage(login_windows_whandle[0][1],win32con.MOUSEEVENTF_LEFTUP,0,None)
    """
    #time.sleep(2)

def add_user():
    pass
#login()
#print("aaaaaaaaa")
#handle =  win32gui.FindWindow(None,"网上股票交易系统5.0")
#windows_list= enum_all_child(whandle)
#print(windows_list)
#sys_treeview32_handle =  find_windows_classname(windows_list,"SysTreeView32")
#print(sys_treeview32_handle)
## 3. 获取根节点
#root = win32api.SendMessage(sys_treeview32_handle[0][1], TVM_GETNEXTITEM, TVGN_ROOT, 0)
#print(root)
#traverse_tree(sys_treeview32_handle[0][1])
#buy_stock("600009",200, 27.15)
#sell_stock("600009",200,27.15)
#query_quantity()
#query_untrade_stock()
#cancel_trade_stock("600100")
#sell_stock('000009', 100, 8.74)
#print(win32process.GetWindowThreadProcessId(2230510))
""""
w_handle=win32gui.FindWindow(None,"同花顺(9.40.60) - 自选股")
child_windows = []
if w_handle != None:
    child_windows = enum_all_child(w_handle)
print(child_windows)
"""