import time
import sys
import os
import itertools
import argparse
import tkinter as tk
import threading
from PIL import Image, ImageTk
from functools import partial
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import snmp as snmp_tool
import history as history_tool
from constants import *

#@brief, indicates if the snmp thread runs and 
#if the whole app shall stop or not
thread_running_ = 1

class sqv_monitor:
    def __init__(self_, window_, tk_, stations_, devices_, device_header_, snmp_):
        # @brief sqv_monitor constructor
        # allocate memory for icons and labels, instanciate the main gui scrollbar
        #@param window_ in - tk root window
        #@param tk_     in - tkinter instance
        #@param stations_ in - stations table
        #@param devices_  in - devices types
        #@param device_header in - devices names
        #@param snmp      in - snmp_getter instance
        #@param
        self_.window_ = window_        # tkinter stuff
        self_.tk_ = tk_                # tkinter stuff
        self_.stations_ = stations_    # map station name / ip address
        self_.devices_ = devices_      # device types
        self_.device_index_ = [i_ for i_ in range(len(devices_))]
        self_.icon_images_ = {}        # images data
        self_.snmp_ = snmp_
        self_.cell_width_ = []
        self_.device_header_ = device_header_
        self_.snmp_lru_values_ = {}     #snmp lru default values
        self_.snmp_lru_states_ = {}     #snmp lru states values 

        #initialize the snmp data map
        for s_ in stations_.keys():
            self_.snmp_lru_values_[s_] = []
            self_.snmp_lru_states_[s_] = []

        #get screen resolution
        _screen_w = window_.winfo_screenwidth()
        _screen_h = window_.winfo_screenheight()
        _extra_space=1.57
        if _screen_w < MIN_WIDTH_RESOLUTION:
            #quit, width resolution is not enough
            print("Minimum resolution required is 1366, your's", _screen_w)
            sys.exit()
        window.resizable(False, False)
        _height = (len(stations_) + _extra_space) * (BOX_HEIGHT + STATE_HEIGHT)
        if _height > HEIGHT_OCCUPATION_RATIO * _screen_h:
            #compute window height
            _height = HEIGHT_OCCUPATION_RATIO * _screen_h

        #create the scrollable container
        self_.frame_scrollable_ = history_tool.ScrollableFrame(self_.window_, height=_height)

        #allocate resources for labels and images
        #-----------------------------------------
        #allocate memory for label icons
        self_.labels_icons_ = [[ self_.tk_.Label(master = self_.frame_scrollable_.scrollable_frame) 
            for i in range(len(devices_))] for j in range(len(stations_.keys()))]

        #allocate memory for state icons
        self_.labels_states_icons_ = [[ self_.tk_.Label(master = self_.frame_scrollable_.scrollable_frame) 
            for i in range(len(devices_))] for j in range(len(stations_.keys()))]

        #allocate memory for station labels
        self_.labels_stations_ = [ self_.tk_.Label(master = self_.frame_scrollable_.scrollable_frame)
            for i in range(len(stations_.keys()))]

        #allocate memory for images
        for i_ in icons_:
            image_ = Image.open(os.path.join('icons', i_))
            if i_ in ('available.png', 'notavailable.png', 'empty.png'):
                self_.icon_images_[i_] = ImageTk.PhotoImage(image_.resize((BOX_WIDTH, STATE_HEIGHT)))
            else:
                self_.icon_images_[i_] = ImageTk.PhotoImage(image_.resize((BOX_WIDTH, BOX_HEIGHT)))

        #allocate resources for the sw version button
        self_.history_image_ = ImageTk.PhotoImage(file=os.path.join('icons', 'history.png'))
        self_.history_b_ = [self_.tk_.Button(
            master = self_.frame_scrollable_.scrollable_frame, 
            image=self_.history_image_, 
            command=partial(history_tool.handle_logs, s_, self_), borderwidth=0)
            for s_ in stations_.keys()]

        #allocate resources for the log events button
        self_.info_image_ = ImageTk.PhotoImage(file=os.path.join('icons', 'info.png'))
        self_.sw_b_ = [self_.tk_.Button(
            master = self_.frame_scrollable_.scrollable_frame, 
            image=self_.info_image_, 
            command=partial(history_tool.handle_sw, s_, self_, self_.snmp_), borderwidth=0)
            for s_ in stations_.keys()]

        #allocate resources fort the about image
        image_ = Image.open(os.path.join('icons', 'Viveris.png'))
        self_.viveris_ = ImageTk.PhotoImage(image_.resize((280,140)))

        #allocate the labels for alignment rows
        self_.scroll_align_labels_ = [ self_.tk_.Label(master = self_.frame_scrollable_.scrollable_frame)
            for i in range(len(devices_) + BOXES_COLUMN)]
        self_.header_align_labels_ = [ self_.tk_.Label(master = self_.window_)
            for i in range(len(devices_) + BOXES_COLUMN)]

        #initialize the alignment cell width array
        for i_ in range(len(devices_) + BOXES_COLUMN):
            if i_ == 0:
                self_.cell_width_.append(MAX_CELL_WIDTH)
            elif i_ in (1,2):
                self_.cell_width_.append(BUTTONS_CELL_WIDTH)
            else:
                self_.cell_width_.append(ICONS_CELL_WIDTH)

    def display_header(self_):
        #@brief display the table header
        #@param in - devive_header_ 1D table with each device type
        #@returns None
        label1_ = self_.tk_.Label(
            master = self_.window_,
            text="Stations", bg=WINDOW_BG, fg=TEXT_FG, font=(TEXT_FONT, STATION_TEXT_SIZE))
        label1_.grid(row=0, column=0, padx=1, pady=0, sticky="NSEW")
        label1_ = self_.tk_.Label(master = self_.window_, bg = WINDOW_BG)
        label1_.grid(row=0, column=1, padx=1, pady=0, sticky="NSEW")
        label1_ = self_.tk_.Label(master = self_.window_, bg = WINDOW_BG)
        label1_.grid(row=0, column=2, padx=1, pady=0, sticky="NSEW")
        # display the header
        # ------------------
        for (col_, dev_ ) in zip(self_.device_index_, self_.device_header_):
            label_h_ = self_.tk_.Label(
                master = self_.window_,
                text=dev_, bg=WINDOW_BG, fg=TEXT_FG, font=(TEXT_FONT, HEADER_TEXT_SIZE))
            label_h_.grid(row=0, column=col_ + BOXES_COLUMN, padx=1, pady=0, sticky="NSWE")
        #display the alignment header
        #---------------------------
        _columns = [i_ for i_ in range(len(self_.header_align_labels_))]
        for (l_, col_, width_) in zip(self_.header_align_labels_, _columns, self_.cell_width_):
            l_.config(width=width_, height=0, bg = WINDOW_BG)
            l_.grid(row=1, column=col_, padx=0, pady=0, sticky="NSWE")

    def display_snmp_data(self_):
        # @brief display snmp data
        # @returns None
        lru_values_ = []
        lru_states_ = []
        rows_ = [i_ for i_ in range(len(self_.stations_.keys()))]
        display_rows_ = [3 + (i_*2) for i_ in range(len(self_.stations_.keys()))]
        
        #display the alignment row
        #-------------------------
        _columns = [i_ for i_ in range(len(self_.scroll_align_labels_))]
        for (l_, _col, _width) in zip(self_.scroll_align_labels_, _columns, self_.cell_width_):
            l_.config(width=_width, height=0, bg=WINDOW_BG)
            l_.grid(row=2, column=_col, padx=0, pady=0, sticky="NSWE")
        #display row by row
        for (   station_, 
                lb_stations_,
                row_,
                display_row_,
                h_button_,
                sw_button_) in \
            zip(
                self_.stations_.keys(), 
                self_.labels_stations_,
                rows_,
                display_rows_,
                self_.history_b_,
                self_.sw_b_,
            ):
            #get the snmp data for this station
            lru_values_ = self_.snmp_lru_values_[station_]
            lru_states_ = self_.snmp_lru_states_[station_]
            # display the station/ip label or not conected
            if lru_values_:
                # the station is connected
                text_color_ = TEXT_FG
                text_l_ = station_ + '\n' + self_.stations_[station_]
            else:
                # the station is not connected
                text_color_ = TEXT_FG_NOT_CONNECTED
                text_l_ = station_ + '\n' + '[not connected]'
                lru_values_ = [NOT_CONNECTED for i in range(len(self_.devices_))]
                lru_states_ = [NOT_CONNECTED for i in range(len(self_.devices_))]
            #display the station name and it's ip address
            lb_stations_.config(
                text = text_l_, fg=text_color_, bg=WINDOW_BG,
                wraplength=STATION_IP_TEXT_SIZE * 10,
                font = (TEXT_FONT, STATION_IP_TEXT_SIZE))
            lb_stations_.grid(row=display_row_, rowspan=2, column=0, padx=0, pady=0, sticky="NSEW")

            #display the history button
            #--------------------------
            h_button_.config(image = self_.history_image_, bg=WINDOW_BG)
            h_button_.grid(row=display_row_, rowspan=2, column=1, padx=0, pady=0, sticky="NSEW")

            #display the sw button
            #---------------------
            sw_button_.config(image = self_.info_image_, bg=WINDOW_BG)
            sw_button_.grid(row=display_row_, rowspan=2, column=2, padx=0, pady=0, sticky="NSEW")
            # display the icon corresponding to each lru value and lru state
            #---------------------------------------------------------------

            columns_ = [i_ + BOXES_COLUMN for i_ in range(len(lru_values_))]
            for (dev_, ldv_, ls_, col_) in zip(self_.devices_, lru_values_, lru_states_, columns_):
                #display lru default values
                self_.display_default_value(dev_, ldv_, row_, col_, display_row_, BOXES_COLUMN)
                #display lru states
                self_.display_lru_state(dev_, ls_, row_, col_, display_row_ + 1, BOXES_COLUMN)
        self_.frame_scrollable_.grid(
            row=3, column=0, columnspan = 14, rowspan = 1, padx=1, pady=0, sticky="NSEW")

    def display_lru_state(self_, device_id_, lru_state_, row_, col_, display_row_, BOXES_COLUMN):
        # @brief display the lru state state according with it's value
        # @param in - device_id  device type
        # @param in - lru_state_ snmp value corresponding to lru state
        # @param in - row_, col_ row/col position
        # #@returns None
        icon2display_ = ""
        if lru_state_ == LRU_STATE_UNAVAILABLE:
            icon2display_ = UNAVAILABLE
        elif lru_state_ == LRU_STATE_AVAILABLE:
            icon2display_ = AVAILABLE
        else:
            icon2display_ = UNKNOWN_LRU_STATE
        label_ = self_.labels_states_icons_[row_][col_ - BOXES_COLUMN] 
        image_ = (self_.icon_images_[icon2display_])
        label_.config(image = image_, bg=WINDOW_BG)
        label_.grid(row=display_row_, column=col_, padx=0, pady=0, sticky="NSEW")        

    def display_default_value(self_, device_id_, lru_value_, row_, col_, display_row_, BOXES_COLUMN):
        # @brief display an icon according with it's device type and the retrieved value
        # @param in - device_id  device type
        # @param in - lru_value_ snmp value corresponding to lru default value
        # @param in - row_, col_ row/col posiition
        # #@returns None
        icon2display_ = ""
        if device_id_ == "UTR":
            icon2display_ = get_utr_icon(lru_value_)
        elif device_id_ == "UTV":
            icon2display_ = get_utv_icon(lru_value_)
        elif device_id_ == "BIR":
            icon2display_ = get_bir_icon(lru_value_)
        elif device_id_ == "UTS":
            icon2display_ = get_uts_icon(lru_value_)
        else:
            icon2display_ = UNKNOWN
        #recover the label and the image to display
        label_ = self_.labels_icons_[row_ ][col_ - BOXES_COLUMN] 
        image_ = (self_.icon_images_[icon2display_])
        label_.config(image = image_, bg=WINDOW_BG)
        label_.grid(row=display_row_, column=col_, padx=0, pady=0, sticky="NSEW")

    def display_about(self_):
        #@brief display the About window
        #@param in - self_  sqv monitor instance
        new_window_ = tk.Toplevel(self_.window_)
        new_window_.transient(self_.window_)
        new_window_.resizable(False, False)
        new_window_.title('A propops')
        new_window_['bg'] = WINDOW_BG
        if os.path.isfile(os.path.join('icons', 'snmpdashboard.png')):
            _image = ImageTk.PhotoImage(file=os.path.join('icons', 'snmpdashboard.png'))
        new_window_.iconphoto(False, _image)
        label1_ = tk.Label(master = new_window_, 
           text='SQV SNMP MONITORING v1.0.0\n\u00a9 2021 Viveris',
           fg=TEXT_FG, bg=WINDOW_BG, font=(TEXT_FONT, HEADER_TEXT_SIZE))
        label1_.grid(row=0, column=0, padx=1, pady=3, sticky="NWSE")
        label2_ = tk.Label(master = new_window_, bg=WINDOW_BG, image=self_.viveris_)
        label2_.grid(row=1, column=0, padx=1, pady=3, sticky="NWSE")
        new_window_.update_idletasks()
        new_window_.update()
#
# icon detection functions
def get_utr_icon(value_):
    if value_ in UTR_CODES_:
        return UTR_CODES_[value_]
    return UNKNOWN

def get_utv_icon(value_):
    if value_ in UTV_CODES_:
        return UTV_CODES_[value_]
    return UNKNOWN

def get_bir_icon(value_):
    if value_ in BIR_CODES_:
        return BIR_CODES_[value_]
    return UNKNOWN

def get_uts_icon(value_):
    if value_ in UTS_CODES_:
        return UTS_CODES_[value_]
    return UNKNOWN

def usage_and_exit():
    print("Usage sqv.exe -f [xml config file]")
    sys.exit()

def retrieve_snmp_data(stations_, snmp_, sqv_, refresh_, checker_):
    # @brief thread retrieving the snmp data
    # @params:
    # @stations_ in - map of stations/ip addresses
    # @snmp_     in - instance for snmp tool
    # @sqv_      in - sqv_monitor instance
    # @refresh_  in - sleep time after iterating through all stations
    # @refresh_  in - instance of check changes class
    global thread_running_
    while thread_running_:
        for s_ in stations_.keys():
            # fill the result with unknown data
            values_ = {snmp_tool.KEY_LRU_States:[], snmp_tool.KEY_LRU_Values:[]}
            # check if the app shall stop
            if thread_running_ == 0:
                break
            ip_address_ = stations_[s_]
            # get the lru number;
            # we shall do this all the time since
            # communication problems might hapens at any time
            items_ = snmp_.get_snmp_single_data(ip_address_, s_, snmp_tool.LRU_OID_)
            if int(items_) > 0:
                # get the rest of the SQV data
                values_ = snmp_.get_snmp_multiple_set(ip_address_, s_, snmp_tool.LRU_OID_, items_)
            # update the values to be displayed
            sqv_.snmp_lru_values_[s_] = values_[snmp_tool.KEY_LRU_Values]
            sqv_.snmp_lru_states_[s_] = values_[snmp_tool.KEY_LRU_States]
            checker_.check_history(values_, s_, sqv_.device_header_)
        time.sleep(refresh_)

def stop_app():
    print("the SQV app will stop in a few seconds..")
    global thread_running_
    thread_running_ = 0

def parse_config_file(file_name_, credentials_, refresh_, stations_ip_map_):
    # @brief parse the input xml file and build the stations/ip map, 
    # and the the snmp connection credentials
    # @paralm in - file_name  xml file name
    # @param out - credentials_  hash
    # @param out - refresh_  the refresh rate
    # @param out - stations_ip_map_  station/ip map
    # @return 0 in case of failure, 1 in case of successful parsing
    ip_ = []
    _stations = []
    _username = []
    _authkey  = []
    _privkey  = []
    _port     = []
    _station = ""
    if not os.path.isfile(file_name_):
        print('cannot open xml config file ' + file_name_)
        return 0
    #parse the xml
    try:
        tree_ = ET.parse(file_name_)
        root_ = tree_.getroot()
    except ParseError as e_:
        formatted_e = str(e_)
        print (formatted_e)
        return 0
    #build the internal data
    for elem_ in root_.iter('name'):
        _stations.append(elem_.text)
    for elem_ in root_.iter('ip'):
        ip_.append(elem_.text)
    for elem_ in root_.iter('port'):
        _port.append(int(elem_.text))
    for elem_ in root_.iter('username'):
        _username.append(elem_.text)
    for elem_ in root_.iter('privkey'):
        _privkey.append(elem_.text)
    for elem_ in root_.iter('authkey'):
        _authkey.append(elem_.text)
    for elem_ in root_.iter('refresh'):
        refresh_.append(int(elem_.text))
    #build the stations map
    #Note:
    #the corectness of the IP address shall be checked
    #otherwise PySNMP issues errors
    if (len(ip_) == len(_stations)) and (len(_stations) == len(_port)) \
    and (len(_port) == len(_username)) and (len(_username) == len(_privkey)) \
    and (len(_privkey) == len(_authkey)):
        for (s_, u_, a_, k_, p_, i_) in zip(_stations, _username, _authkey, _privkey, _port, ip_):
            if s_ in stations_ip_map_:
                print('The station name ' + s_ + ' is already present in the configuration')
                return 0
            stations_ip_map_[s_] = i_
            credentials_[s_] = {'username':u_,
                                'authkey':a_,
                                'privkey':k_,
                                'port':p_}
        return 1
    else:
        print('inconsistecy concerning the credentials, please check the port, username, authkey and private keys')
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Add long and short argument
    parser.add_argument("--file", "-f", dest ="config_file", help="specify input config file")
    # Read arguments from the command line
    args = parser.parse_args()
    # Check for xml file
    if args.config_file:
        auth_data_ = {}
        refresh_ = []
        stations_map_ = {}
        if not parse_config_file(args.config_file, auth_data_, refresh_, stations_map_):
            sys.exit()

        #initialize GUI
        window = tk.Tk()
        window.title('SQV SNMP MONITORING')
        window['bg'] = WINDOW_BG

        #define a handler for the exit button
        window.protocol("WM_DELETE_WINDOW", stop_app)

        #instanciate a snmp tool object
        snmp_ = snmp_tool.snmp_getter(auth_data_)

        #instanciate app
        sqv = sqv_monitor(window, tk, stations_map_, devices_, grid_header_, snmp_)

        #define a menu
        _menubar = tk.Menu(window)
        _filemenu = tk.Menu(_menubar, tearoff=0)
        _filemenu.add_command(label="A propos", command=sqv.display_about)
        _filemenu.add_separator()
        _filemenu.add_command(label="Exit", command=stop_app)
        _menubar.add_cascade(label="Aide", menu=_filemenu)
        window.config(menu=_menubar)

        #display only the header and the left column
        sqv.display_header()

        #instanciate the check changes class
        checker_ = history_tool.check_changes()

        # start the snmp thread
        thread_ = threading.Thread(
            target=retrieve_snmp_data, 
            args = (stations_map_, snmp_, sqv, refresh_[0], checker_))
        thread_.start()

        #load the window icon
        if os.path.isfile(os.path.join('icons', 'snmpdashboard.png')):
            _image = ImageTk.PhotoImage(file=os.path.join('icons', 'snmpdashboard.png'))
            window.iconphoto(False, _image)

        while thread_running_:
            sqv.display_snmp_data()
            window.update_idletasks()
            window.update()
            time.sleep(0.07)   #lower the cpu consumption
        thread_.join()
    else:    
        usage_and_exit()