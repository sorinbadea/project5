#file containing constants for GUI

# constants for the main window (sqv)
# some fonts, text sizes and colors
STATION_IP_TEXT_SIZE  = 11
HEADER_TEXT_SIZE      = 13
STATION_TEXT_SIZE     = 14
TEXT_FONT             = "Helvetica"
TEXT_FG               = 'navy'
TEXT_FG_NOT_CONNECTED = 'gray50'
LRU_STATE_UNAVAILABLE = 2
LRU_STATE_AVAILABLE   = 1
NOT_CONNECTED         = 0xFF
UNAVAILABLE           = "notavailable.png"
AVAILABLE             = "available.png"
UNKNOWN               = "unknown.png"
UNKNOWN_LRU_STATE     = "empty.png"
#window sizing parameters
OFFSET_               = 3
MAX_CELL_WIDTH        = 14
BUTTONS_CELL_WIDTH    = 6
ICONS_CELL_WIDTH      = 13
HEIGHT_OCCUPATION_RATIO = 0.8
MIN_WIDTH_RESOLUTION    = 1366
BOX_WIDTH = 72
BOX_HEIGHT = 56
STATE_HEIGHT = 5
# utv codes hash map
UTV_CODES_ = { 0 :  "failure.png",
               1 :  "power.png",
               80 : "master.png",
               81 : "slave.png",
             }
# utv codes hash map
UTS_CODES_ = { 0  : "failure.png",
               80 : "ok.png",
             }
# utr codes hash map
UTR_CODES_ = { 0  : "failure.png",
               1  : "power.png",
               80 : "ok.png",
             }
# bir codes hash map
BIR_CODES_ = { 0  : "failure.png",
               1  : "power.png",
               80 : "ok.png",
             }
grid_header_ = [
            "QUAI 1\nUTV 1",
            "QUAI 1\nUTV 2",
            "QUAI 1\nBIR A",
            "QUAI 1\nBIR B",
            "QUAI 1\nUTR",
            "QUAI 2\nUTV 1",
            "QUAI 2\nUTV 2",
            "QUAI 2\nBIR A",
            "QUAI 2\nBIR B",
            "QUAI 2\nUTR",
            "UTS" ]
sw_devices_ = [
            "QUAI 1\nUTV 1",
            "QUAI 1\nUTV 2",
            "QUAI 2\nUTV 1",
            "QUAI 2\nUTV 2",
            "UTS",
            "QUAI 1\nBIR A",
            "QUAI 1\nBIR B",
            "QUAI 2\nBIR A",
            "QUAI 2\nBIR B" ]
devices_ = [
            "UTV", "UTV", "BIR","BIR","UTR", "UTV", "UTV", "BIR", "BIR", "UTR", "UTS",
           ]
icons_ = [
           'failure.png', 'master.png', 'ok.png', 'power.png', 'slave.png', 'unknown.png',
           'empty.png', 'available.png', 'notavailable.png'
         ]
#modal window constants
#text sizes
WAITING_MESSAGE = 'please wait while fetching data'
LOG_DIRECTORY   = 'history'
SW_VERSION_TEXT_SIZE = 13
EVENTS_TEXT_SIZE     = 11
WAIT_TEXT_SIZE       = 11
FONT_COLOR=TEXT_FG
SEPARATOR = ' new value '
MIN_LOG_ELEMENTS = 7
TS_LRU_TABLE_SIZE = 4
PROD_INFO_TABLE_SIZE = 2
STATE_SERVICES_TABLE_SIZE = 2
header_group_sw_ = [ 'devices', 'software']
header_product_ = [ 'prod', 'description']
prod_tags_ =   ['prodName', 'prodPresentation']
header_states_ = ['state', 'value']
state_tags_ =  ['stateTimeStampLRU', 'stateMIBdataAvailable', 'stateServiceDescr', 'stateServiceState' ]
NA_FONT_COLOR = 'red'