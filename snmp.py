import os
from pysnmp.hlapi import *
# as per MIB descripton the lru useful info set consists in 4 values
# 1. lru index
# 2. lru state
# 3. lru description
# 4. lru default state
USEFUL_SET_              = 4
LRU_DEAFULT_STATE_INDEX_ = 3 #(0 index table)
LRU_STATE_INDEX_         = 2 #(0 index table)
LRU_OID_  = "1.3.6.1.4.1.13933.100.3.1.0"
KEY_LRU_States = 'lru_states'
KEY_LRU_Values = 'lru_values'
# as per MIB descripton the sw version info set consists in 5 values
# 1. sw index
# 2. sw description
# 3. sw location
# 4. sw editor
# 5. sw version
SW_OID_   = "1.3.6.1.4.1.13933.100.2.1.0"
SW_VERSION_START_INDEX_ = 4
SW_VERSION_USEFUL_SET_ = 5
# as per MIB desription the state description set consists in 3 values
# 1. stateServiceIndex
# 2. stateServiceDescr
# 3. stateServiceState
STATE_SERVICE_DESCR_SET_ = 3
STATE_SERVICE_DESCR_INDEX_ = 1
PROD_NAME_OID_      = "1.3.6.1.4.1.13933.100.1.0"
TIME_STAMP_LRU_OID_ = "1.3.6.1.4.1.13933.100.8.2"
STATE_NUMBER_OID_   = "1.3.6.1.4.1.13933.100.8.6.0"

def get_snmp_next_cmd(_auth_data_, _ip_, _oid_, _rows_):
    #@brief execute a SNMP command
    #@param _auth_data_ -in authentication data
    #@param _ip_   in IP address
    #@param _oid_  in OID 
    #@param _rows_ in nb of items to retrieve
    if _ip_ == "localhost":
        #dbug mode, connect with a v2 snmp agent
        community = CommunityData('public')
    else:
        community = UsmUserData(
            _auth_data_['username'],
            _auth_data_['authkey'],
            _auth_data_['privkey'],
            usmHMACSHAAuthProtocol,
            usmAesCfb128Protocol
            )
    return nextCmd(
        SnmpEngine(),
        community,
        UdpTransportTarget((_ip_, _auth_data_['port'],), timeout=2, retries=0),
        ContextData(),
        ObjectType(ObjectIdentity(_oid_)),
        maxRows=(_rows_)
        )
#
# this module implements the snmp part of the sqv project
# 
class snmp_getter:

    def __init__(self_, auth_data_):
        # @brief
        # snmp_getter constructor
        # store the authentication map
        self_.auth_data_ = auth_data_

    def get_snmp_single_data(self_, ip_, station_, oid_):
        # @brief get the number of lru devices
        # @params in - ip station ip address
        # @params in - oid_ asn1 oid for lru number
        result_ = 0
        _auth_data_ = self_.auth_data_[station_]
        print(ip_ + " get data from oid:" + oid_)
        if ip_ == "localhost":
            #dbug mode, connect with a v2 snmp agent
            community = CommunityData('public')
        else:
            community = UsmUserData(
                _auth_data_['username'],
                _auth_data_['authkey'],
                _auth_data_['privkey'],
                usmHMACSHAAuthProtocol,
                usmAesCfb128Protocol
                )
        iterator_ = getCmd(
            SnmpEngine(),
            community,
            UdpTransportTarget((ip_, _auth_data_['port'],), timeout=2, retries=0),
            ContextData(),
            ObjectType(ObjectIdentity(oid_)),
            )
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator_)
        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                #print(' = '.join([x.prettyPrint() for x in varBind]))
                result_ = varBind[1]
                break
        return result_
        
    def get_snmp_multiple_set(self_, ip_, station_, oid_, items_):
        # @brief retrive in one shot the lru states and the lru default values
        # @params in - ip station ip address
        # @params in - station_ station name
        # @params in - oid_ asn1 oid for lru info
        # @returns two table containing the 
        # lru states andf the lru default state
        lru_def_values_ = []
        lru_state_values_ = []
        _auth_data_ = self_.auth_data_[station_]
        #lru states arrives before lru default values
        lru_def_values_start_ = items_ * LRU_DEAFULT_STATE_INDEX_
        lru_state_start_  = items_ * LRU_STATE_INDEX_
        counter_ = 0
        print(ip_ + " Retrive snmp data from oid:" + oid_)
        iterator_ = get_snmp_next_cmd(_auth_data_, ip_, oid_, (items_ * USEFUL_SET_))
        for errorIndication, errorStatus, errorIndex, varBinds in iterator_:
            if errorIndication:
                print(errorIndication)
                break
            elif errorStatus:
                print('%s at %s' % (errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                break
            else:
                for varBind in varBinds:
                    #print(' = '.join([x.prettyPrint() for x in varBind]))
                    if counter_ >= lru_state_start_ and counter_ < lru_def_values_start_:
                        lru_state_values_.append(varBind[1])
                    if counter_ >= lru_def_values_start_:
                        # start saving lru default values
                        lru_def_values_.append(varBind[1])
                    counter_ += 1
        return  {KEY_LRU_States: lru_state_values_ , KEY_LRU_Values: lru_def_values_}
        
    def get_snmp_single_set(self_, ip_, station_, oid_, items_, data_set_=0, data_index_=0):
        # @brief retrive a set of snmp data
        # @params in - ip station ip address
        # @params in - station station name
        # @params in - oid asn1 oid for sw version
        # @param  in - items_ nb of items in set
        # @param - optional - data_set, the length of one set
        # @param - optional - data_index, start of snmp data
        # @returns a table containing the requested set
        values_ = []
        _auth_data_ = self_.auth_data_[station_]
        counter_ = sw_start_ = 0
        #check the optional parameters
        if data_index_:
            sw_start_  = items_ * data_index_
        if data_set_:
            items_ *= data_set_
        print(ip_ + " Retrive snmp data from oid:" + oid_)
        iterator_ = get_snmp_next_cmd(_auth_data_, ip_, oid_, items_)
        for errorIndication, errorStatus, errorIndex, varBinds in iterator_:
            if errorIndication:
                print(errorIndication)
                break
            elif errorStatus:
                print('%s at %s' % (errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                break
            else:
                for varBind in varBinds:
                    if counter_ >= sw_start_:
                        # start saving data
                        values_.append(varBind[1])
                    counter_ += 1
        return  values_
#
# Note
# ----
# these are the expectd oids to recover in case of 2 lru
#(typically you will get 11 LRU's)
#
# "1.3.6.1.4.1.13933.100.3.2.1.1.1", #lru 1 index
# "1.3.6.1.4.1.13933.100.3.2.1.1.2", #lru 2 index
# "1.3.6.1.4.1.13933.100.3.2.1.2.1", #lru description 1 (UTV 1)
# "1.3.6.1.4.1.13933.100.3.2.1.2.2", #lru description 2 (UTV 2)
# "1.3.6.1.4.1.13933.100.3.2.1.3.1", #lru 1 state
# "1.3.6.1.4.1.13933.100.3.2.1.3.2", #lru 2 state
# "1.3.6.1.4.1.13933.100.3.2.1.4.1", #lru default Code 1
# "1.3.6.1.4.1.13933.100.3.2.1.4.2", #lru default Code 1