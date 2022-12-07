from datetime import datetime
import random
import numpy as np
import pandas as pd
# from matplotlib.font_manager import FontProperties
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
import plotly.express as px

# warnings.filterwarnings('ignore') # 要求忽略warning
import matplotlib.pyplot as plt

# import debugpy                # thread中設debug中斷點所需
# debugpy.debug_this_thread()   # thread中設debug中斷點所需
plt.style.use('ggplot')   # 設定畫圖風格為ggplot
plt.rcParams['font.sans-serif'] = ['SimHei'] # 設定相容中文 
plt.rcParams['axes.unicode_minus'] = False
pd.options.mode.chained_assignment = None

class WorkThread(QThread):
    signal_action = Signal(str)
    signal_df_result = Signal(pd.DataFrame)
    signal_df_gantt = Signal(pd.DataFrame)
    signal_fig_gantt = Signal(object) 
    signal_list_dsl = Signal(list) 

    def __init__(self, date, workbill_df, machine_df, priority_df, mold_df, gantt_df, parameter_list):
        super().__init__()
        self.date = date
        self.workbill_df_ori = workbill_df
        self.machine_df = machine_df
        self.priority_df = priority_df
        self.mold_df = mold_df
        self.gantt_df = gantt_df
        self.c_m, self.c_c, self.alpha_c, self.prior_2, self.prior_3 = parameter_list

        self.workbill_df = pd.DataFrame()
        self.remain_workbill_df = pd.DataFrame()
        self.Weighted_selection_df = pd.DataFrame()
        self.result_df = pd.DataFrame()
        self.gantt_df_Chinese = pd.DataFrame()
        self.co_molding_df = pd.DataFrame()
        self.co_molding_list = []
        self.drop_bill_list = []
        self.Device_schedule_list = []
        self.gantt_fig = None
        self.co_molding_bool = True

    def run(self):
        try:
            self.signal_action.emit('載入資料中...')
            # 【處理self.workbill_df】
            self.workbill_df_ori.loc[:, 'endTime'] = pd.to_datetime(self.workbill_df_ori.loc[:, 'endTime'])
            self.workbill_df_ori.loc[:, 'endTime_s'] = (self.workbill_df_ori.loc[:, 'endTime'] - datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')).dt.total_seconds().astype(int)
            self.workbill_df_ori.loc[:, 'p_time_ori'] = (self.workbill_df_ori.loc[:, 'cycletime'] * self.workbill_df_ori.loc[:, 'qty'] / self.workbill_df_ori.loc[:, 'hold']).apply(np.ceil).astype(int)
            self.workbill_df_ori.loc[:, 'd-p'] = self.workbill_df_ori.loc[:, 'endTime_s'] - self.workbill_df_ori.loc[:, 'p_time_ori']
            self.workbill_df_ori.loc[:, 'd-p_date'] = pd.to_timedelta(self.workbill_df_ori.loc[:, 'd-p'], unit = 's') + datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')
            self.workbill_df_ori.loc[:, 'p_time_real'] = None
            self.workbill_df_ori.loc[:, 'b_time'] = 0
            self.workbill_df_ori.loc[:, 'c_time'] = None
            self.workbill_df_ori.loc[:, 'apply_machine'] = None
            self.workbill_df_ori.loc[:, 'delay'] = None

            # 【共模】決定共模群組的保留單與其餘單
            if self.co_molding_bool: # 只要有關共模，都要先加此判斷條件
                for uni_mold in self.workbill_df_ori.loc[:, 'moldNo'].unique(): # 遍歷模具，拉出相同模具的資料為mold_sub_data，並以交期急迫時(d-p)排序
                    used_bill = []   # 用於置放同一模具下已經組成群組而不能再考慮的訂單
                    mold_sub_data = self.workbill_df_ori.loc[self.workbill_df_ori['moldNo'] == uni_mold].sort_values(by = ['d-p'])
                    mold_sub_data.reset_index(drop = True, inplace = True)
                    if len(mold_sub_data) > 1:
                        for row in range(len(mold_sub_data)): # 同模具有超過1張訂單時，遍歷每一張訂單(row)
                            keep_bill = mold_sub_data.loc[row, 'billNo'] # 保留單(若達成條件則記錄)
                            if keep_bill not in used_bill:
                                keep_dp = mold_sub_data.loc[row, 'd-p']
                                other_bill, group_bill = [], [keep_bill] # 其餘單與群組單
                                if row < (len(mold_sub_data) - 1):       # 遍歷row(最早)之後的單，須達成下列條件：三天內的交期急迫時差距、同色同料、不同產品(群組中)、尚未組成群組的單
                                    for sub_row in range(row + 1, len(mold_sub_data)):
                                        if (mold_sub_data.loc[sub_row, 'd-p'] < keep_dp + 60 * 60 * 24 * 3) & \
                                        (mold_sub_data.loc[sub_row, 'colorNo'] == mold_sub_data.loc[row, 'colorNo']) & \
                                        (mold_sub_data.loc[sub_row, 'materialNo'] == mold_sub_data.loc[row, 'materialNo']) & \
                                        (mold_sub_data.loc[sub_row, 'productNo'] not in mold_sub_data.loc[mold_sub_data['billNo'].isin(group_bill), 'productNo'].values) & \
                                        (mold_sub_data.loc[sub_row, 'billNo'] not in mold_sub_data.loc[mold_sub_data['billNo'].isin(used_bill), 'billNo'].values):
                                            other_bill.append(mold_sub_data.loc[sub_row, 'billNo'])
                                            group_bill.append(mold_sub_data.loc[sub_row, 'billNo'])
                                used_bill += group_bill
                                if len(group_bill) > 1: # 確定成為共模群組，建立其餘單清單(self.drop_bill_list)、記錄共模群組的表格(self.co_molding_list)(初始工時為群組中最大者)
                                    self.drop_bill_list += other_bill
                                    self.co_molding_list.append([uni_mold, keep_bill, other_bill, group_bill, self.workbill_df_ori.loc[self.workbill_df_ori['billNo'].isin(group_bill), 'p_time_ori'].max()])
                self.co_molding_df = pd.DataFrame(self.co_molding_list, columns = ['moldNo', 'keep_billNo', 'remain_billNo', 'group_billNo', 'p_time_ori'])
                # 從原本的訂單資料中，分成【預先排的訂單】與【其餘單】
                self.workbill_df = self.workbill_df_ori.loc[~self.workbill_df_ori['billNo'].isin(self.drop_bill_list), :]
                self.remain_workbill_df = self.workbill_df_ori.loc[self.workbill_df_ori['billNo'].isin(self.drop_bill_list), :]
                self.remain_workbill_df.reset_index(drop = True, inplace = True)
            else:
                self.workbill_df = self.workbill_df_ori
            # ↑↑↑↑↑↑↑↑↑ 共模 ↑↑↑↑↑↑↑↑↑↑

            self.workbill_df = self.workbill_df.sort_values(by = ['d-p'])
            self.workbill_df.reset_index(drop = True, inplace = True)

            # 【處理self.machine_df】
            for j in range(len(self.machine_df)):
                if type(self.machine_df.loc[j, 'start_working_date']) is str:
                    if pd.to_datetime(self.machine_df.loc[j, 'start_working_date']) < datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S'):
                        self.machine_df.iloc[j, 2:] = np.nan    # 如果有機台的start_working_date早於排程時間(self.date)，則清除資訊
                else: pass
        except:
            self.signal_action.emit('無法載入資料，請檢查資料內容是否有誤')
        else:
            self.signal_action.emit('計算中...')
            # (內部使用，使用度少可不管) 【工單權值計算表格】
            self.Weighted_selection_df = pd.DataFrame(columns = ['Job'] + [i for i in self.machine_df['machineNo']])
            self.Weighted_selection_df['Job'] = self.workbill_df['billNo']

            # (內部使用) 【記錄每台機檯目前生產結束前生產的工單、材料、顏色與待機時間點】
            for row in range(len(self.machine_df)):
                info_dict = {}
                info_dict['machineNo'] = self.machine_df.loc[row, 'machineNo']
                if (str(self.machine_df.loc[row, 'start_working_date']) != 'nan'):
                    #已有在生產的機台
                    info_dict['colorNo'] = [self.machine_df.loc[row, 'colorNo']]
                    info_dict['materialNo'] = [self.machine_df.loc[row, 'materialNo']]
                    info_dict['Job'] = [None]
                    info_dict['c_time'] = [int((pd.to_datetime(self.machine_df.loc[row, 'start_working_date']) - datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')).total_seconds())]
                else:
                    info_dict['colorNo'] = [None]
                    info_dict['materialNo'] = [None]
                    info_dict['Job'] = [None]
                    info_dict['c_time'] = [0]
                info_dict['mold'] = [None]
                self.Device_schedule_list.append(info_dict)
            
            
            if len(self.machine_df) < len(self.workbill_df):
                for j in range(len(self.workbill_df)):
                    material_change_booling, color_change_booling = None, None
                    # 訂單對各機台的權值：初始工時/機台良率
                    # 【共模】若屬於共模群組，則初始工時使用該群組最大者(已紀錄)，否則使用訂單自己計算的結果
                    if (self.co_molding_bool) & (self.workbill_df.loc[j, 'billNo'] in self.co_molding_df['keep_billNo'].values):
                        weighted = self.co_molding_df.loc[self.co_molding_df['keep_billNo'] == self.workbill_df.loc[j, 'billNo'], 'p_time_ori'].values / self.machine_df.loc[:, 'yield'].values
                    else:
                        weighted = self.workbill_df.loc[j, 'p_time_ori'] / self.machine_df.loc[:, 'yield'].values
                    
                    # 【權值：新增考慮換色/換料】(逐機台比對)
                    for device_num in range(len(self.Device_schedule_list)):
                        if (self.Device_schedule_list[device_num]['colorNo'][-1] == None) & (self.Device_schedule_list[device_num]['materialNo'][-1] == None):
                            pass    # 先確認一開始機台有沒有生產產品，若color跟material都是None代表沒有，則可以直接排
                        else:
                            color_change_booling = self.workbill_df.loc[j, 'colorNo'] != self.Device_schedule_list[device_num]['colorNo'][-1]  # 比較該機台目前生產使用的顏色/原料
                            material_change_booling = self.workbill_df.loc[j, 'materialNo'] != self.Device_schedule_list[device_num]['materialNo'][-1]  # 同上
                            if color_change_booling & ~material_change_booling:                # 僅換色
                                weighted[device_num] = weighted[device_num] * self.alpha_c + self.c_c
                            elif ~color_change_booling & material_change_booling:              # 僅換料
                                weighted[device_num] = weighted[device_num] + self.c_m
                            elif color_change_booling & material_change_booling:               # 換色又換料
                                weighted[device_num] = weighted[device_num] * self.alpha_c + self.c_m
                            else: # 都沒有換：維持
                                pass
                    
                    # 【權值：新增考慮換模】
                    for device_num in range(len(self.Device_schedule_list)):
                        if (self.Device_schedule_list[device_num]['mold'][-1] == None):  # 前一個模具紀錄是None: 單純上模
                            weighted[device_num] += self.mold_df.loc[self.mold_df['moldNo'] == self.workbill_df.loc[j, 'moldNo'], 't_load'].values[0] * 60    
                        else:
                            if (self.Device_schedule_list[device_num]['mold'][-1] != self.workbill_df.loc[j, 'moldNo']):  # 需要換模，加當下單的上模時間，與前一單的下模時間
                                weighted[device_num] += (
                                    self.mold_df.loc[self.mold_df['moldNo'] == self.workbill_df.loc[j, 'moldNo'], 't_load'].values[0] * 60 + \
                                        self.mold_df.loc[self.mold_df['moldNo'] == self.Device_schedule_list[device_num]['mold'][-1], 't_off'].values[0] * 60
                                )
                            else: # 都沒有換：維持
                                pass
                    
                    print('********')
                    print(self.workbill_df)
                    print('********')
                    print(self.machine_df)
                    print('********')
                    print(self.priority_df)
                    print('********')
                    print(self.mold_df)
                    print('********')

                    # 【權值：新增考慮客戶對機台的優先順位】
                    try:
                        P1, P2, P3 = self.priority_df[self.priority_df['productNo'] == self.workbill_df.loc[j, 'productNo']].values[0][1:] 
                        if P1 != P1: P1 = '' # 查找是否有NA
                        if P2 != P2: P2 = ''
                        if P3 != P3: P3 = ''
                        P1_index = [self.machine_df.loc[:, 'machineNo'].values.tolist().index(i) for i in P1.split(',')] if len(P1) > 0 else [] # 將逗號文字字串轉化為list
                        P2_index = [self.machine_df.loc[:, 'machineNo'].values.tolist().index(i) for i in P2.split(',')] if len(P2) > 0 else []
                        P3_index = [self.machine_df.loc[:, 'machineNo'].values.tolist().index(i) for i in P3.split(',')] if len(P3) > 0 else []
                        None_index = [i for i in list(range(len(self.machine_df))) if i not in P1_index + P2_index + P3_index]
                        weighted[P1_index] = weighted[P1_index]                   # 最優先順位
                        weighted[P2_index] = weighted[P2_index] * self.prior_2    # 第二三順位需增加權重
                        weighted[P3_index] = weighted[P3_index] * self.prior_3        
                        weighted[None_index] = weighted[None_index] * 10000       # 不在順位列表者，表示確定無緣，應乘上大數
                    except:
                        # debugpy.breakpoint()  # thread中設debug中斷點
                        print('異常')
                    else:                        
                        # 【選擇機台】每個機台的待機時間點與權值加起來，選擇最小者
                        device_sct = [i['c_time'][-1] for i in self.Device_schedule_list] # 提取目前所有機台的c_time(待機時間點)
                        device_sct_weighted_sum = device_sct + weighted                   # 待機時間加入權值，最低者為所要填入工單的機台
                        select_device = [index for index, i in enumerate(device_sct_weighted_sum) if i == device_sct_weighted_sum.min()]
                        # 若'不幸'同時有兩個以上的機台權值總值相同，則隨機取一
                        # if len(select_device) > 1: select_device = random.choice(select_device)
                        # else: select_device = select_device[0]
                        # debugpy.breakpoint()
                        select_device = select_device[0]
                        
                        # 【計算起始時間與實際工時】選定機台後插單，先依照機台跟訂單預設
                        device_now_b_time = device_sct[select_device]
                        device_now_p_time = self.workbill_df.loc[j, 'p_time_ori']/self.machine_df.loc[select_device, 'yield']
                        
                        # 【共模】若屬於共模群組，則計算共模的工時與實際剩餘單的工時(分別用於實際繪圖與結果表格)
                        if (self.co_molding_bool) & (self.workbill_df.loc[j, 'billNo'] in self.co_molding_df['keep_billNo'].values):
                            device_now_p_time_co_molding = (self.co_molding_df.loc[self.co_molding_df['keep_billNo'] == self.workbill_df.loc[j, 'billNo'], 'p_time_ori'].values / self.machine_df.loc[select_device, 'yield'])[0]
                            device_now_remain_p_time = ( self.remain_workbill_df.loc[self.remain_workbill_df['billNo'].isin(self.co_molding_df.loc[self.co_molding_df['keep_billNo'] == self.workbill_df.loc[j, 'billNo'], 'remain_billNo'].values[0]), 'p_time_ori'] / self.machine_df.loc[select_device, 'yield'] ).values
                        else: device_now_p_time_co_molding, device_now_remain_p_time = 0, 0
                        
                        # 【換色/換料】一樣需要考慮共模的情況
                        if (self.Device_schedule_list[select_device]['colorNo'][-1] == None) & (self.Device_schedule_list[select_device]['materialNo'][-1] == None):
                            pass
                        else:
                            color_change_booling = self.workbill_df.loc[j, 'colorNo'] != self.Device_schedule_list[select_device]['colorNo'][-1]
                            material_change_booling = self.workbill_df.loc[j, 'materialNo'] != self.Device_schedule_list[select_device]['materialNo'][-1]
                            if color_change_booling & ~material_change_booling: #僅換色
                                device_now_p_time += self.c_c
                                if (self.co_molding_bool) & (self.workbill_df.loc[j, 'billNo'] in self.co_molding_df['keep_billNo'].values): 
                                    device_now_p_time_co_molding += self.c_c
                                    device_now_remain_p_time += self.c_c
                            elif ~color_change_booling & material_change_booling: #僅換料
                                device_now_p_time += self.c_m
                                if (self.co_molding_bool) & (self.workbill_df.loc[j, 'billNo'] in self.co_molding_df['keep_billNo'].values): 
                                    device_now_p_time_co_molding += self.c_m
                                    device_now_remain_p_time += self.c_m
                            elif color_change_booling & material_change_booling: #換色又換料
                                device_now_p_time += max(self.c_m, self.c_c)
                                if (self.co_molding_bool) & (self.workbill_df.loc[j, 'billNo'] in self.co_molding_df['keep_billNo'].values): 
                                    device_now_p_time_co_molding += max(self.c_m, self.c_c)
                                    device_now_remain_p_time += max(self.c_m, self.c_c)
                            else: #維持
                                pass    

                        # 【換模實際時間影響】影響的是開始時間，而非工作時間
                        if (self.Device_schedule_list[select_device]['mold'][-1] == None):    # 前一個模具紀錄是None: 單純上模
                            device_now_b_time += self.mold_df.loc[self.mold_df['moldNo'] == self.workbill_df.loc[j, 'moldNo'], 't_load'].values[0] * 60
                        else:
                            if (self.Device_schedule_list[select_device]['mold'][-1] != self.workbill_df.loc[j, 'moldNo']):  # 需要換模，加當下單的上模時間，與前一單的下模時間
                                device_now_b_time += (
                                    self.mold_df.loc[self.mold_df['moldNo'] == self.workbill_df.loc[j, 'moldNo'], 't_load'].values[0] * 60 + \
                                        self.mold_df.loc[self.mold_df['moldNo'] == self.Device_schedule_list[select_device]['mold'][-1], 't_off'].values[0] * 60
                                )
                            else: # 都沒有換：維持
                                pass

                        # 【排單完成】批次紀錄結果
                        self.workbill_df.loc[j, 'p_time_real'] = device_now_p_time
                        self.workbill_df.loc[j, 'apply_machine'] = self.machine_df.loc[select_device, 'machineNo']
                        self.workbill_df.loc[j, 'b_time'] = device_now_b_time
                        # print(device_now_b_time)
                        self.workbill_df.loc[j, 'c_time'] = device_now_b_time + device_now_p_time
                        self.Weighted_selection_df.iloc[j, 1:] = weighted # 似乎可以省略
                        self.Device_schedule_list[select_device]['Job'].append(self.workbill_df.loc[j, 'billNo'])
                        self.Device_schedule_list[select_device]['colorNo'].append(self.workbill_df.loc[j, 'colorNo'])
                        self.Device_schedule_list[select_device]['materialNo'].append(self.workbill_df.loc[j, 'materialNo'])
                        self.Device_schedule_list[select_device]['mold'].append(self.workbill_df.loc[j, 'moldNo'])
                        ## 【共模】有在共模群組的保留單，時間需要使用device_now_p_time_co_molding；剩餘單在此也各自依群組批次紀錄結果
                        if (self.co_molding_bool) & (self.workbill_df.loc[j, 'billNo'] in self.co_molding_df['keep_billNo'].values):
                            self.Device_schedule_list[select_device]['c_time'].append(device_now_b_time + device_now_p_time_co_molding)
                            self.remain_workbill_df.loc[self.remain_workbill_df['billNo'].isin(self.co_molding_df.loc[self.co_molding_df['keep_billNo'] == self.workbill_df.loc[j, 'billNo'], 'remain_billNo'].values[0]), 'p_time_real'] = device_now_remain_p_time
                            self.remain_workbill_df.loc[self.remain_workbill_df['billNo'].isin(self.co_molding_df.loc[self.co_molding_df['keep_billNo'] == self.workbill_df.loc[j, 'billNo'], 'remain_billNo'].values[0]), 'apply_machine'] = self.machine_df.loc[select_device, 'machineNo']
                            self.remain_workbill_df.loc[self.remain_workbill_df['billNo'].isin(self.co_molding_df.loc[self.co_molding_df['keep_billNo'] == self.workbill_df.loc[j, 'billNo'], 'remain_billNo'].values[0]), 'b_time'] = device_now_b_time
                            self.remain_workbill_df.loc[self.remain_workbill_df['billNo'].isin(self.co_molding_df.loc[self.co_molding_df['keep_billNo'] == self.workbill_df.loc[j, 'billNo'], 'remain_billNo'].values[0]), 'c_time'] = device_now_b_time + device_now_remain_p_time
                        else:
                            self.Device_schedule_list[select_device]['c_time'].append(self.workbill_df.loc[j, 'c_time'])
            
            # 【計算延遲】若考慮共模，則剩餘單也要準備好，並且與原本的訂單合併
            self.workbill_df.loc[:, 'delay'] = self.workbill_df.loc[:, 'c_time'] - self.workbill_df.loc[:, 'endTime_s'] 
            if (self.co_molding_bool) & (pd.isna(self.remain_workbill_df['c_time']).sum() == 0):
                self.remain_workbill_df.loc[:, 'delay'] = self.remain_workbill_df.loc[:, 'c_time'] - self.remain_workbill_df.loc[:, 'endTime_s']
                self.workbill_df = self.workbill_df.append(self.remain_workbill_df)   # 如果沒有加上這兩行，就不會出現共模保留以外的訂單
                self.workbill_df.reset_index(drop = True, inplace = True)             # 同上
            
            # 【結果表格】
            self.result_df = self.workbill_df.copy()
            self.result_df.loc[:, 'b_time'] = pd.to_timedelta(self.result_df.loc[:, 'b_time'], unit = 's') + datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')
            self.result_df.loc[:, 'c_time'] = pd.to_timedelta(self.result_df.loc[:, 'c_time'], unit = 's') + datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')
            self.result_df.loc[:, 'p_time_ori'] = pd.to_timedelta(self.result_df.loc[:, 'p_time_ori'], unit = 's')
            self.result_df.loc[:, 'p_time_real'] = pd.to_timedelta(self.result_df.loc[:, 'p_time_real'], unit = 's')
            self.result_df.loc[:, 'delay'] = pd.to_timedelta(self.result_df.loc[:, 'delay'], unit = 's')
            self.result_df = self.result_df[['billNo', 'productNo', 'endTime', 'cycletime', 'qty', 'hold', 'colorNo', 'materialNo', 'moldNo', 'p_time_ori', 'd-p_date', 'p_time_real', 'b_time', 'c_time', 'apply_machine', 'delay']]

            # 【甘特圖表格】如果是首次排單，self.gantt_df筆數為0，可直接建立；否則要用合併的方式處理
            gantt_df_prepare = self.workbill_df[['billNo', 'b_time', 'c_time', 'apply_machine', 'qty', 'hold', 'productNo', 'colorNo', 'materialNo', 'moldNo']]
            gantt_df_prepare.loc[:, 'b_time'] = pd.to_timedelta(gantt_df_prepare.loc[:, 'b_time'], unit = 's') + datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')
            gantt_df_prepare.loc[:, 'c_time'] = pd.to_timedelta(gantt_df_prepare.loc[:, 'c_time'], unit = 's') + datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')
            gantt_df_prepare.loc[:, 'billNo'] = gantt_df_prepare.loc[:, 'billNo'].astype(str)
            gantt_df_prepare.rename({'b_time': 'Start', 'c_time': 'Complete', 'apply_machine': 'device'}, axis = 1, inplace=True)

            if len(self.gantt_df) == 0:
                self.gantt_df = gantt_df_prepare
            else:
                self.gantt_df = self.gantt_df.append(gantt_df_prepare)
                self.gantt_df.reset_index(drop = True, inplace = True)

            # 回傳給主程式
            self.signal_action.emit('排單完成')
            self.signal_df_result.emit(self.result_df)
            self.signal_df_gantt.emit(self.gantt_df)
            self.signal_list_dsl.emit(self.Device_schedule_list)

            # 轉中文版
            self.gantt_df_Chinese = self.gantt_df.copy()
            self.gantt_df_Chinese.columns = ['訂單編號', '開始時間', '結束時間', '分派機台', '產品數量', '模穴數', '產品編號', '顏色編號', '原料編號', '模具編號']

            self.gantt_fig = px.timeline(
                self.gantt_df_Chinese, 
                x_start = '開始時間',
                x_end = '結束時間',
                y = '分派機台',
                hover_name = '訂單編號', 
                hover_data = ['產品數量', '模穴數', '產品編號', '顏色編號', '原料編號', '模具編號'],
                color = '訂單編號',
                color_discrete_sequence = px.colors.qualitative.Pastel,
                text = '訂單編號',
            )
            self.signal_fig_gantt.emit(self.gantt_fig)
            # debugpy.breakpoint()
