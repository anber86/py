#trade_date,open,high,low,close,pct_ch,vol
class ZoneNode:
    def __init__(self):
        self.date=None
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.pct_ch = None
        self.vol = None
        self.top_flage=None
        self.up_node = None
        self.down_node  = None
        self.same_left_node = None
        self.same_right_node = None

class slash_node:
    def _init_(self):
        self.left_zone=None
        self.right_zone=None
        self.top_index=None
        self.top_vlue=None
        self.slash_node_next=None
        self.slash_node_up=None
