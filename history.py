import os
import time
import struct
import time
import functools
from datetime import datetime
from PIL import Image, ImageTk
import itertools
import tkinter as tk
import re
import snmp as snmp_tool
from constants import *

def window_initialization(window_, fav_icon_):
    #@brief initialize the sw version or the log viewer window
    #@param window_ in - parent window
    #@fav_icon_     in - icon on top left
    new_window_ = tk.Toplevel(window_)
    new_window_.transient(window_)
    new_window_.resizable(False, False)
    new_window_.title('SQV SNMP MONITORING')
    #load the fav icon
    if os.path.isfile(os.path.join('icons', 'snmpdashboard.png')):
        _image = ImageTk.PhotoImage(file=os.path.join('icons', fav_icon_))
        new_window_.iconphoto(False, _image)
    return new_window_

class ScrollableFrame(tk.Frame):
    #@brief initialize a scrollbar;
    #it is used for the main window as well as the event window
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        #check for width and/or height
        if 'height' in kwargs and 'width' in kwargs:
            canvas = tk.Canvas(self, width=kwargs['width'], height=kwargs['height'])
        if 'height' in kwargs:
            canvas = tk.Canvas(self, height=kwargs['height'])
        if 'width' in kwargs:
            canvas = tk.Canvas(self, width=kwargs['width'])
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview, width=12)
        self.scrollable_frame = tk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0,0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class check_changes():
    #@brief - this class check any changes in the snmp data;
    #if changes are detected the information is logged;
    def __init__(self_):
        #initialize historic values
        self_._h_lru_values = {}
        self_._h_lru_states = {}
        
    def check_history(self_, values_, station_, devices_):
        # check for changes in values_ vs previous values
        # @param in - values_ a hash of tables containing 
        #             lru states and lru default values
        # @param in - station_ station name
        # @param in - devices, sw devices
        #returns None

        #get the snmp data for this station, this values could be truncated!
        lru_values_ = values_[snmp_tool.KEY_LRU_Values]
        lru_states_ = values_[snmp_tool.KEY_LRU_States]

        if station_ in self_._h_lru_values:
            #lrus values already presents, get the historic values
            _old_values = [ self_._h_lru_values[station_][_i] for _i in range(len(self_._h_lru_values[station_]))]
            for (val, ov, dev) in zip(lru_values_, _old_values, devices_):
                # compare incomming data length with the 
                # data already received
                #print ("history value", val, "incomming value", self_._h_lru_values[station_][_i])
                if (val != ov):
                    record_change(station_, dev, val, 'lruDefaultCode')

        if station_ in self_._h_lru_states:
            # lrus values already presents
            _old_values = [ self_._h_lru_states[station_][_i] for _i in range(len(self_._h_lru_states[station_]))]
            for (val, ov, dev) in zip(lru_states_, _old_values, devices_):
                # compare incomming data length with the 
                # data already received
                #print ("history state", val, "incomming value", self_._h_lru_states[station_][_i])
                if (val != ov):
                    record_change(station_, dev, val, 'lruState')

        #update historic values
        if len(lru_values_) > 0:
            self_._h_lru_values[station_] = lru_values_
        if len(lru_states_) > 0:
            self_._h_lru_states[station_] = lru_states_

def record_change(station_, device_name_, value_, who_):
    # @brief alert about a parameter change
    # update report the file history/[station name.log]
    # @param in - station_ station name
    # @param in - device_name_  the name of the device_name_
    # @param in - value_  vale that changed
    # @param in - who_ lruDefaultCode or lruState
    _now = datetime.now()
    _dt = _now.strftime("%d/%m/%Y %H:%M:%S")
    device_name_ = device_name_.replace('\n', ' ')
    _str = _dt + " " + who_ + " " + device_name_ + SEPARATOR + str(value_)
    print(_str)
    #append data in file
    try:
        if not os.path.exists(LOG_DIRECTORY):
            os.makedirs(LOG_DIRECTORY)
        _f_name = station_ + '.log'
        _file = open(os.path.join(LOG_DIRECTORY, _f_name),'a')
        _file.write(_str + '\n')
        _file.close()
    except OSError:
        print ("Could not open log file, please check your permissions")

#############################################################################
###                sw info and log viewer button handlers                 ###
#############################################################################
def display_label_wait(_master):
    #@brief display the waiting message
    label_wait_ = tk.Label(master = _master, text=WAITING_MESSAGE, 
        fg=FONT_COLOR, font=(TEXT_FONT, WAIT_TEXT_SIZE))
    label_wait_.grid(row=0, column=0, padx=3, columnspan=2, pady=3, sticky="NW")
    _master.update_idletasks()
    _master.update()
    return label_wait_

def handle_sw(station_, sqv_instance_, snmp_):
    # display the sw installed on this station
    # @param in - station  station name
    # @param in - sqv_instance_  sqv_monitor object
    # @param in - snmp_  snmp_getter object
    #station label
    new_window_ = window_initialization(sqv_instance_.window_, 'snmpdashboard.png')
    label_wait_ = display_label_wait(new_window_)
    label_wait_.config(text=station_, fg=FONT_COLOR, font=(TEXT_FONT, STATION_TEXT_SIZE))
    label_wait_.grid(row=0, column=0, padx=3, pady=3, sticky="NW")

    #display SW group header at row 1 and column 0
    display_group_header(new_window_, 1, 0, header_group_sw_)
    #display product group header at row 1 and column 2
    display_group_header(new_window_, 1, 2, header_product_)
    #display states group header at row >5 and column 2
    display_group_header(new_window_, 5, 2, header_states_)

    #recover the sw version
    _ip = sqv_instance_.stations_[station_]
    _items = snmp_.get_snmp_single_data(_ip, station_, snmp_tool.SW_OID_)
    _sw_table = snmp_.get_snmp_single_set(
        _ip, station_, 
        snmp_tool.SW_OID_, _items, snmp_tool.SW_VERSION_USEFUL_SET_, snmp_tool.SW_VERSION_START_INDEX_)

    #recover the product name and product description
    _prod_info = []
    _states = []
    _service_states = []
    _prod_info = snmp_.get_snmp_single_set(_ip, station_,
        snmp_tool.PROD_NAME_OID_, PROD_INFO_TABLE_SIZE)
    #recover the mib states data
    _states = snmp_.get_snmp_single_set(_ip, station_,
        snmp_tool.TIME_STAMP_LRU_OID_, TS_LRU_TABLE_SIZE)
    #_items = snmp_.get_snmp_single_data(_ip, station_, snmp_tool.STATE_NUMBER_OID_)
    #(for the moment we will consider one item for service state)
    _items = 1
    #recover the product states data
    _service_states = snmp_.get_snmp_single_set(
        _ip, station_,
        snmp_tool.STATE_NUMBER_OID_, _items, snmp_tool.STATE_SERVICE_DESCR_SET_, snmp_tool.STATE_SERVICE_DESCR_INDEX_)

    #display sw version group on row 2 and column 0
    #-------------------------------------------
    display_group(new_window_, 2, 0, sw_devices_, _sw_table, 'v')

    #display product name, prod description on row 2 and column 2
    #------------------------------------------------------------
    display_group(new_window_, 2, 2, prod_tags_, _prod_info, '')

    #display states and TS at row 6, column 2
    #----------------------------------------
    _states_2_display=[]
    if len(_states) == TS_LRU_TABLE_SIZE:
        _states_2_display.append(get_ts_lru_and_mib_available(_states[0]))
        _states_2_display.append(get_available_state(_states[3]))
    if len(_service_states) == STATE_SERVICES_TABLE_SIZE:
        _states_2_display.append(_service_states[0])
        _states_2_display.append(get_available_state(_service_states[1]))
    display_group(new_window_, 6, 2, state_tags_, _states_2_display, '')

    new_window_.update_idletasks()
    new_window_.update()
    return 1

def display_group_header(window_, row_, col_, header_):
    _columns = [ col_ + _i for _i in range(len(header_))]
    for (_text, _col) in zip(header_, _columns):
        _label = tk.Label(master = window_,
            text=_text, fg=FONT_COLOR, font=(TEXT_FONT, HEADER_TEXT_SIZE, 'underline'))
        _label.grid(row=row_, column=_col, padx=8, pady=3, sticky="NW")

def display_group(window_, start_row_, col_, tags_, result_, prefix_):
    rows_ = [start_row_ + _i for _i in range(len(tags_))]
    #display the tags
    for (dev_, row_ ) in zip (tags_, rows_):
        dev_ = dev_.replace('\n', ' ')
        _label = tk.Label(master = window_,
            text=dev_, fg='black', font=(TEXT_FONT, SW_VERSION_TEXT_SIZE))
        _label.grid(row=row_, column=col_, padx=8, pady=3, sticky="NW")
    #display resulted data
    for (dev_, sw_, row_) in zip(tags_, result_, rows_):
        _label = tk.Label(master = window_,
        text=prefix_ + sw_, fg=FONT_COLOR, font=(TEXT_FONT, SW_VERSION_TEXT_SIZE))
        _label.grid(row=row_, column=col_ + 1, padx=8, pady=3, sticky="NW")
    #display remaing data as NA
    rest_rows = [start_row_ + len(result_) + _i for _i in range(len(tags_) - len(result_))]
    for _row in rest_rows:
        _label = tk.Label(master = window_,
            text='N.A.', fg=NA_FONT_COLOR, font=(TEXT_FONT, SW_VERSION_TEXT_SIZE))
        _label.grid(row=_row, column=col_ + 1, padx=8, pady=3, sticky="NW")

def get_ts_lru_and_mib_available(input_bytes_):
    #@brief compute the state stateTimeStampUrl and stateMibDataAvailable
    stateTimeStampLru     = 'N.A.'
    #input bytes are in big endian, keep only the first 4 as the time stamp 
    #is represented on 4 bytes, Note: the SNMP agent is BIG endian
    _bytes = bytes(input_bytes_)[0:4]
    ts_stateTimeStampLru = int.from_bytes((_bytes), byteorder='big')
    ts_stateTimeStampLru -= (70*31556926) #the snmp agent uses 1900 as ts reference
    try:
        stateTimeStampLru = time.ctime(ts_stateTimeStampLru)
    except OSError:
        stateTimeStampLru = 'N.A.'
    return stateTimeStampLru

def get_available_state(state_):
    #@brief compute the state service state
    if state_ == 1:
        return 'Available'
    elif state_ == 2:
        return 'Unavailable'
    else:
        return '[Unknown]'

def handle_logs(station_, sqv_instance_):
    # @brief display the change logs for one station
    # @param in - station  station name
    # @param in - sqv instance sqv_monitor instance class
    try:
        new_window_ = window_initialization(sqv_instance_.window_, 'snmpdashboard.png')
        label_wait_ = display_label_wait(new_window_)
        label_wait_.config(text=station_, fg=FONT_COLOR, font=(TEXT_FONT, STATION_TEXT_SIZE))
        label_wait_.grid(row=0, column=0, padx=8, pady=3, sticky="NW")
        _f_name = station_ + '.log'
        _file = open(os.path.join(LOG_DIRECTORY, _f_name),'r')
        _lines = _file.readlines()
        _file.close()
        _header_text = [ 'time stamp', 'element', 'device', 'value']
        _cols = [_i for _i in range(len(_header_text))]
        _width_t = [14, 11, 12, 4]
        for (_col, _text, _width) in zip (_cols, _header_text, _width_t):
            label_ = tk.Label(master = new_window_,
            text=_text, width = _width, fg=FONT_COLOR, font=(TEXT_FONT, HEADER_TEXT_SIZE, 'underline'))
            label_.grid(row=1, column=_col, padx=0, pady=3, sticky="NW")
        #load the scrolable area
        frame_s = ScrollableFrame(new_window_, width=446)
        _rows = [2 + _i for _i in range(len(_lines))]
        for (_line, _row) in zip(_lines, _rows):
            if _line == "\n":
                next
            #extract the time stamp, the value that change, the device name and it's new value
            display_line(frame_s, _line, _row)
        frame_s.grid(row=2, column=0, columnspan = 5, rowspan = 10, padx=8, pady=3, sticky="NW")
    except OSError:
        #there are no changes recorded for this file
        label_wait_.config(text ="\nThere are no recorded events for " + station_ + '\n',
                    fg=FONT_COLOR, font=(TEXT_FONT, HEADER_TEXT_SIZE))
    new_window_.update_idletasks()
    new_window_.update()
    return 1

def display_line(frame, line, row_):
    #split a line and extract the usefull data
    #@param in - frame  - in master frame
    #@param in - line log line
    #@row_   in - display row
    _table = line.split(" ")
    _column=0
    if (len(_table) >= MIN_LOG_ELEMENTS):
        _column= 2
        _ts = _table[0] + ' ' + _table[1]
        _element = _table[2]
        tk.Label(master=frame.scrollable_frame,
            text=_ts, font=(TEXT_FONT, EVENTS_TEXT_SIZE)).grid(row=row_, column=0, padx=8, sticky="NW")
        tk.Label(master=frame.scrollable_frame,
            text=_element, font=(TEXT_FONT, EVENTS_TEXT_SIZE)).grid(row=row_, column=1, padx=8, sticky="NW")
        _device_and_values = re.split('lruState|lruDefaultCode', line)
        if len(_device_and_values) == 2:
            _dev_and_value = _device_and_values[1].split(SEPARATOR, 2)
            if len(_dev_and_value) == 2:
                tk.Label(master=frame.scrollable_frame,
                    text=_dev_and_value[0], font=(TEXT_FONT, EVENTS_TEXT_SIZE)).grid(row=row_, padx=8, column=2, sticky="NW")
                tk.Label(master=frame.scrollable_frame,
                    text=_dev_and_value[1], font=(TEXT_FONT, EVENTS_TEXT_SIZE)).grid(row=row_, padx=8, column=3, sticky="NW")
                return
    #unexpecetd line format
    tk.Label(master=frame.scrollable_frame,
        text='incoherent line', fg='red', font=(TEXT_FONT, EVENTS_TEXT_SIZE)).grid(row=row_, column=_column, padx=8, sticky="NW")