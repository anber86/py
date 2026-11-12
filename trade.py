import win32api
import win32gui
import time
import win32con 
import win32process
import psutil
import pyperclip
import win32com.client
from pywinauto import Application
import ctypes
from ctypes import wintypes
import win32clipboard
import subprocess
windows_hand=[]
pid=0
trade_select=False
account_information={}
#run_name_sefot = "C:\同花顺软件\同花顺\xiadan.exe"
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
# 消息常量
WM_SETTEXT = win32con.WM_SETTEXT        # 设置编辑框文字
WM_GETTEXT = win32con.WM_GETTEXT        # 获取编辑框文字
WM_GETTEXTLENGTH = win32con.WM_GETTEXTLENGTH
CB_SELECTSTRING = 0x014C    # 查找并选中列表内匹配文本的项（配合WM_SETTEXT最常用）
CB_GETCURSEL    = 0x0147    # 获取当前选中索引
CB_SETCURSEL    = 0x0146    # 通过索引选中一项
CB_GETLBTEXT    = 0x0148    # 根据索引拿列表项文字
CB_SHOWDROPDOWN = 0x014F    # 展开/收起下拉框
CB_GETCOUNT     = 0x0145    # 获取列表总条数
CB_FINDSTRINGEXACT=0x0158   #是完全匹配kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
DWORD = wintypes.DWORD
HANDLE = wintypes.HANDLE
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MAX_PATH = 260
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]
def kill_by_pid(pid):
    try:
        p = psutil.Process(pid)
        p.kill()
        return True
    except psutil.NoSuchProcess:
        print("进程不存在")
        return False
    except Exception as e:
        print(e)
        return False
def activate_window(title):
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        print("窗口未找到")
        return False
    # 最小化则还原
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    # 解决SetForegroundWindow限制
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    win32gui.SetForegroundWindow(hwnd)
    return True
def get_hwnds_by_pid_win32(pid, only_visible=True):
    hwnd_list = []
    def cb(hwnd, param):
        tid, wp = win32process.GetWindowThreadProcessId(hwnd)
        if wp == pid:
            if only_visible and not win32gui.IsWindowVisible(hwnd):
                return True
            hwnd_list.append(hwnd)
        return True
    win32gui.EnumWindows(cb, None)
    return hwnd_list
def get_pids_by_exe(exe_name: str) -> list[int]:
    """根据exe名称查找所有PID，如 "notepad.exe" """
    exe_name = exe_name.lower()
    pids_buf = (DWORD * 1024)()
    cb = ctypes.sizeof(pids_buf)
    cb_returned = DWORD()
    ret = []

    if not psapi.EnumProcesses(ctypes.byref(pids_buf), cb, ctypes.byref(cb_returned)):
        return ret
    count = cb_returned.value // ctypes.sizeof(DWORD)

    for i in range(count):
        pid = pids_buf[i]
        hproc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not hproc:
            continue
        hmod = wintypes.HMODULE()
        needed = DWORD()
        if psapi.EnumProcessModulesEx(hproc, ctypes.byref(hmod), ctypes.sizeof(hmod), ctypes.byref(needed), 0x03):
            buf = ctypes.create_unicode_buffer(MAX_PATH)
            psapi.GetModuleBaseNameW(hproc, hmod, buf, MAX_PATH)
            if buf.value.lower() == exe_name:
                ret.append(pid)
        kernel32.CloseHandle(hproc)
    return ret

class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPCWSTR),
        ("lpDesktop", wintypes.LPCWSTR),
        ("lpTitle", wintypes.LPCWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]

def run_createprocess(exe_path:str):
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    pi = PROCESS_INFORMATION()
    ok = kernel32.CreateProcessW(
        exe_path,
        None,
        None,
        None,
        False,
        0,
        None,
        None,
        ctypes.byref(si),
        ctypes.byref(pi)
    )
    if ok:
        pid = pi.dwProcessId
        # 用完记得关闭句柄
        kernel32.CloseHandle(pi.hThread)
        kernel32.CloseHandle(pi.hProcess)
        return True, pid
    return False, 0
def is_running(proc_name:str) -> bool:
    for p in psutil.process_iter(['name']):
        try:
            if p.info['name'].lower() == proc_name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False
def run_trade_sefot():
    global pid
    global windows_hand
    if not(is_running("xiadan.exe")):
        res, pid = run_createprocess(r"C:\同花顺软件\同花顺\xiadan.exe")
        print(res, pid)
        return 
    else:
        pid=get_pids_by_exe("xiadan.exe")[0]
        kill_by_pid(pid)
        res, pid = run_createprocess(r"C:\同花顺软件\同花顺\xiadan.exe")
        print(res, pid)
        return 
def move_window_to_center(hwnd): 
    """
    将指定句柄的窗口移动到屏幕中心，窗口大小保持不变
    :param hwnd: 窗口句柄 int
    :return: True成功 / False失败
    """
    # 获取窗口原有矩形
    rc = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rc)):
        print(f"GetWindowRect 失败，错误码: {kernel32.GetLastError()}")
        return False

    win_w = rc.right - rc.left
    win_h = rc.bottom - rc.top

    # 获取主屏幕分辨率
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)

    # 计算新左上角坐标
    new_x = (screen_w - win_w) // 2
    new_y = (screen_h - win_h) // 2

    # 移动窗口，不改变大小
    if not user32.MoveWindow(hwnd, new_x, new_y, win_w, win_h, True):
        print(f"MoveWindow 失败，错误码: {kernel32.GetLastError()}")
        return False
    return True
def get_direct_child(parent_hwnd):
    lst = []
    h = 0
    while True:
        h = win32gui.FindWindowEx(parent_hwnd, h, None, None)
        if h == 0:
            break
        lst.append(h)
    return lst
def find_windows_classname(hadle,name):
    temp1=[]
    for val in hadle:
        cls_name = win32gui.GetClassName(val)
        tile=win32gui.GetWindowText(val)
        temp1.append((val,cls_name,tile))
    temp=[]
    #print(temp1)
    for val in temp1:
        if name in val[1]:
            temp.append(val[0])
            #print(val)
    return temp
def get_windows_tile(hadle):
    tile=win32gui.GetWindowText(hadle)
    return tile
def get_control_title(hwnd):
    if not win32gui.IsWindow(hwnd):
        return ""
    # WM_GETTEXTLENGTHW 获取宽字符长度
    text_len = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
    if text_len <= 0:
        return ""
    # 宽字符缓冲区，每个字符占2字节
    buf = bytearray((text_len + 2) * 2)
    # WM_GETTEXTW = 0x000D 宽文本消息
    win32gui.SendMessage(hwnd, 0x000D, text_len + 1, buf)
    # 按双字节0截断，转utf16-le
    raw = bytes(buf).split(b'\x00\x00')[0]
    try:
        return raw.decode("utf-16le").strip()
    except Exception:
        # 兜底GBK
        return raw.decode("utf-16le", errors="ignore").strip()
def send_keys_to_edit(hwnd, text):
    #win32gui.SetFocus(hwnd)
    # Ctrl+A 全选
    text = str(text)
    win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
    win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, ord('A'), 0)
    win32gui.SendMessage(hwnd, win32con.WM_KEYUP, ord('A'), 0)
    win32gui.SendMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)
    # Delete
    win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_DELETE, 0)
    win32gui.SendMessage(hwnd, win32con.WM_KEYUP, win32con.VK_DELETE, 0)
    # 逐个字符发送
    for c in text:
        win32gui.SendMessage(hwnd, win32con.WM_CHAR, ord(c), 0)

def get_clip_powershell():
    """旁路读取，不受延迟渲染、剪贴板锁影响"""
    try:
        out = subprocess.check_output(
            ["powershell", "-Command", "Get-Clipboard -Raw"],
            encoding="utf-8",
            timeout=3
        )
        return out
    except Exception:
        return ""

def get_edit_by_clipboard(hwnd):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.CloseClipboard()
    left,top,right,bottom=win32gui.GetWindowRect(hwnd)
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
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,0,0,0,0)
    x=x+40
    y=y+60
    win32api.SetCursorPos((x,y))
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    temp =  get_clip_powershell()
    return temp

def select_simulate_trade(select=trade_select):
    global pid,windows_hand
    run_trade_sefot()
    time.sleep(7)
    windows_hand= (get_hwnds_by_pid_win32(pid))
    #print(windows_hand)
    temp=get_direct_child(windows_hand[1])
    temp1=[]
    for val in temp:
        cls_name = win32gui.GetClassName(val)
        tile=win32gui.GetWindowText(val)
        temp1.append((val,cls_name,tile))
    #print(temp1)
    handle=0
    for vl1,vl2,vl3 in temp1:
        if vl3=="证券公司:":
            #combo_set_cursel(vl1,0)
            handle=vl1
            break
            #rint(combo_select_string(vl1,"模拟炒"))
            #print("aaaaaaaa")
            #print(get_combo_selected_item(vl1))
    # 获取窗口矩形 (left, top, right, bottom)
    #print(f"handle:{handle}")
    left, top, right, bottom = win32gui.GetWindowRect(handle)
    cx = ((left + right) )// 2 + (right-left )
    cy = (top + bottom) // 2 
    #print((top,bottom))

    win32api.SetCursorPos((cx, cy))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    if select==True:
        cy=cy+1*(bottom-top)
        win32api.SetCursorPos((cx, cy))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    else:
        cy=cy+2*(bottom-top)
        #print((top,bottom))
        win32api.SetCursorPos((cx, cy))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    for vl1,vl2,vl3 in temp1:
        if vl3=="登录":
            left, top, right, bottom = win32gui.GetWindowRect(vl1)
            cx = ((left + right) )//2
            cy = (top + bottom) // 2 
            win32api.SetCursorPos((cx, cy))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(10)
    windows_hand= (get_hwnds_by_pid_win32(pid))
    print(f"windows_hand:{windows_hand}")
def query_untrade_stock():
    global windows_hand
    global pid
    list_temp=[] 
    dic_temp ={"证券代码": 0, "股票名": 0, "委托价格": 0, "撤单数量":0}
    windows_handle=windows_hand[1]
    win32gui.ShowWindow(windows_handle,win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_handle,win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(windows_handle)
    time.sleep(5)
    move_window_to_center(windows_handle)
    win32gui.SetWindowPos(windows_handle,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    win32api.keybd_event(win32con.VK_F3,0,0,0)
    win32api.keybd_event(win32con.VK_F3,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(3)
    windows_list = get_direct_child(windows_handle)
    #print(windows_list)
    windows_list = find_windows_classname(windows_list, "AfxMDIFrame")
    windows_list = get_direct_child(windows_list[0])
    windows_list = find_windows_classname(windows_list, "#32770")
    windows_list = get_direct_child(windows_list[1])
    windows_list = find_windows_classname(windows_list, "Afx:")
    windows_list = get_direct_child(windows_list[0])
    windows_list = find_windows_classname(windows_list, "AfxWnd")
    windows_list = get_direct_child(windows_list[0])
    #print(windows_list)
    left,top,right,bottom=win32gui.GetWindowRect(windows_list[0])
    x = left+ (right-left) // 2
    y = top + 20
    while True:
        y = y + 20
        win32api.SetCursorPos((x,y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
        time.sleep(3)
        proces_windows_handle=get_hwnds_by_pid_win32(pid)
        #print(f"proces_windows_handle{proces_windows_handle}")
        windows_handle=windows_hand[0]
        if proces_windows_handle[0] == windows_handle:
            #print("proces_windows_handle[0]=windows_handle")
            break
        curr_windows_handle =get_direct_child(proces_windows_handle[0])
        #print(curr_windows_handle)
        butt_list = find_windows_classname(curr_windows_handle,"Button")
        #print(f"butt_list:{butt_list}")
        static_list = find_windows_classname(curr_windows_handle,"Static")
        #print(f"static_list:{static_list}")
        n = len(static_list)
        name = get_control_title(static_list[(n-3)])
        #print(f"name{name}")
        prices = get_control_title(static_list[(n-2)])
        #print(f"prices{prices}")
        count = get_control_title(static_list[(n-1)])
        #print(f"count{count}")
        dic_temp["证券代码"]= (name.replace("证券代码：",""))[:6].strip()
        dic_temp["股票名"] = (((name.replace("证券代码：",""))[6:])[1:]).strip()
        dic_temp["委托价格"]=(prices.replace("委托价格：","")).strip()
        dic_temp["撤单数量"] = (count.replace("撤单数量：","")).replace("（以实际撤单数量为准）","").strip()
        list_temp.append(dic_temp.copy())
        left,top,right,bottom=win32gui.GetWindowRect(butt_list[1])
        x1=(left+right)//2
        y1=(top+bottom)//2
        win32api.SetCursorPos((x1,y1))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
        time.sleep(2)
        print(f"untrade_stock:{list_temp}")
    #untrade_stock=list_temp
    return list_temp
#print(query_untrade_stock())
def cancel_trade_stock(id:str):
    global windows_hand,pid
    untrad_stock = query_untrade_stock()
    windows_hand= (get_hwnds_by_pid_win32(pid))
    print(f"concel_trade_stock:windows_hand:{windows_hand}")
    windows_handle=windows_hand[1]
    win32gui.ShowWindow(windows_handle,win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_handle,win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(windows_handle)
    time.sleep(3)
    move_window_to_center(windows_handle)
    win32gui.SetWindowPos(windows_handle,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    win32api.keybd_event(win32con.VK_F3,0,0,0)
    win32api.keybd_event(win32con.VK_F3,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(2)
    windows_list = get_direct_child(windows_handle)
    #print(windows_list)
    windows_list = find_windows_classname(windows_list, "AfxMDIFrame")
    windows_list = get_direct_child(windows_list[0])
    windows_list = find_windows_classname(windows_list, "#32770")
    windows_list = get_direct_child(windows_list[1])
    windows_list = find_windows_classname(windows_list, "Afx:")
    windows_list = get_direct_child(windows_list[0])
    windows_list = find_windows_classname(windows_list, "AfxWnd")
    windows_list = get_direct_child(windows_list[0])
    #print(windows_list)
    left,top,right,bottom=win32gui.GetWindowRect(windows_list[0])
    x = left+ (right-left) // 2
    y = top + 20
    c = 1
    for stock in untrad_stock:
        if stock["证券代码"] == id:
            win32api.SetCursorPos((x,(y+c*20)))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
            time.sleep(3)
            proces_windows_handle=get_hwnds_by_pid_win32(pid)
            print(f"proces_windows_handle{proces_windows_handle}")
            windows_handle=windows_hand[0]
            if proces_windows_handle[0] == windows_handle:
                print("proces_windows_handle[0]=windows_handle")
                break
            curr_windows_handle =get_direct_child(proces_windows_handle[0])
            #print(curr_windows_handle)
            butt_list = find_windows_classname(curr_windows_handle,"Button")
            print(f"butt_list:{butt_list}")
            left,top,right,bottom=win32gui.GetWindowRect(butt_list[0])
            x1=(left+right)//2
            y1=(top+bottom)//2
            win32api.SetCursorPos((x1,y1))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
        c = c+1
def query_account_information():
    global windows_hand,account_information
    windows_handle=windows_hand[1]
    win32gui.ShowWindow(windows_handle,win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_handle,win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(windows_handle)
    time.sleep(2)
    move_window_to_center(windows_handle)
    win32gui.SetWindowPos(windows_handle,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    win32api.keybd_event(win32con.VK_F4,0,0,0)
    win32api.keybd_event(win32con.VK_F4,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(10)
    windows_list = get_direct_child(windows_handle)
    windows_list=find_windows_classname(windows_list,"AfxMDIFrame")
    print(windows_list)
    windows_list = get_direct_child(windows_list[0])
    windows_list=find_windows_classname(windows_list,"#32770")
    windows_list = get_direct_child(windows_list[0])
    windows_list=find_windows_classname(windows_list,"Static")
    #print(windows_list)
    #print(get_windows_tile(windows_list[11]))
    account_information["资金余额"] = get_windows_tile(windows_list[11])
    account_information["冻结金额"] = get_windows_tile(windows_list[12])
    account_information["可用金额"] = get_windows_tile(windows_list[13])
    account_information["可取金额"] = get_windows_tile(windows_list[29])
    account_information["股票市值"] = get_windows_tile(windows_list[30])
    account_information["总 资 产"] = get_windows_tile(windows_list[31])
    account_information["持仓盈亏"]  = get_windows_tile(windows_list[59])
    account_information["当日盈亏"]  = get_windows_tile(windows_list[61])
    account_information["当日盈亏比"] = get_windows_tile(windows_list[63])
    print(f"account_information:{account_information}")
def buy_sell_input_trade(stock_id:str, quantity:int, price:float):
    global pid
    windows_list = get_direct_child(windows_hand[1])
    windows_list = find_windows_classname(windows_list,"AfxMDIFrame")
    windows_list = get_direct_child(windows_list[0])
    windows_list = find_windows_classname(windows_list,"#32770")
    windows_list = get_direct_child(windows_list[1])
    edit_list = find_windows_classname(windows_list,"Edit")
    button_list = find_windows_classname(windows_list,"Button")
    left,top,right,bottom=win32gui.GetWindowRect(edit_list[0])
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
    send_keys_to_edit(edit_list[0],stock_id)
    time.sleep(0.5)
    left,top,right,bottom=win32gui.GetWindowRect(edit_list[1])
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
    send_keys_to_edit(edit_list[1],price)
    left,top,right,bottom=win32gui.GetWindowRect(edit_list[2])
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
    send_keys_to_edit(edit_list[2],quantity)
    left,top,right,bottom=win32gui.GetWindowRect(button_list[0])
    x=(left+right)//2
    y=(top+bottom)//2
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(1)
    proces_windows_handle=get_hwnds_by_pid_win32(pid)
    butt_list = find_windows_classname(get_direct_child(proces_windows_handle[0]),"Button")
    print(butt_list) 
    left,top,right,bottom=win32gui.GetWindowRect(butt_list[0])
    x=(left+right)//2
    y=(top+bottom)//2
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
    time.sleep(1)   
    return 0 
def buy_stock(stock_id:str, quantity:int, price:float):
    global windows_hand
    win32gui.ShowWindow(windows_hand[1],win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_hand[1],win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(windows_hand[1])  
    time.sleep(2)
    move_window_to_center(windows_hand[1])
    win32gui.SetWindowPos(windows_hand[1],win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    win32api.keybd_event(win32con.VK_F1,0,0,0)
    win32api.keybd_event(win32con.VK_F1,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(2)
    buy_sell_input_trade(stock_id,quantity,price)
    return 0
def sell_stock(stock_id:str, quantity:int, price:float):
    global windows_hand
    #top_handle = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(windows_hand[1],win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_hand[1],win32con.SW_RESTORE)
    #if top_handle != windows_handle:
    win32gui.SetForegroundWindow(windows_hand[1])
    time.sleep(2)
    move_window_to_center(windows_hand[1])
    win32gui.SetWindowPos(windows_hand[1],win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    time.sleep(0.5)
    win32api.keybd_event(win32con.VK_F2,0,0,0)
    time.sleep(0.05)
    win32api.keybd_event(win32con.VK_F2,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(2)
    buy_sell_input_trade(stock_id, quantity, price)
    return 0
def query_stock_price(stock_id:str)->float:
    global windows_hand
    #top_handle = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(windows_hand[1],win32con.SW_MINIMIZE)
    win32gui.ShowWindow(windows_hand[1],win32con.SW_RESTORE)
    #if top_handle != windows_handle:
    win32gui.SetForegroundWindow(windows_hand[1])
    time.sleep(2)
    move_window_to_center(windows_hand[1])
    win32gui.SetWindowPos(windows_hand[1],win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
    time.sleep(0.5)
    win32api.keybd_event(win32con.VK_F2,0,0,0)
    time.sleep(0.05)
    win32api.keybd_event(win32con.VK_F2,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(2)
    #global pid
    windows_list = get_direct_child(windows_hand[1])
    windows_list = find_windows_classname(windows_list,"AfxMDIFrame")
    windows_list = get_direct_child(windows_list[0])
    windows_list = find_windows_classname(windows_list,"#32770")
    windows_list = get_direct_child(windows_list[1])
    edit_list = find_windows_classname(windows_list,"Edit")
    button_list = find_windows_classname(windows_list,"Button")
    left,top,right,bottom=win32gui.GetWindowRect(edit_list[0])
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
    send_keys_to_edit(edit_list[0],stock_id)
    time.sleep(0.5)
    left,top,right,bottom=win32gui.GetWindowRect(edit_list[1])
    x=(left+right)//2
    y=(top+bottom)//2
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
    time.sleep(0.3)
    temp = float(get_edit_by_clipboard(edit_list[1]).strip())
    return temp
