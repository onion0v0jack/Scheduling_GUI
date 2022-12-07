# importing required modules
from PySide2 import QtCore
from mplWidget import MplWidget
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from thread import *
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt 

plt.style.use('ggplot')   # 設定畫圖風格
plt.rcParams['font.sans-serif'] = ['SimHei'] # 設定相容中文 
plt.rcParams['axes.unicode_minus'] = False
pd.options.mode.chained_assignment = None

QtCore.QCoreApplication.addLibraryPath(os.path.join(os.path.dirname(QtCore.__file__), 'plugins'))  # 掃plugin套件(windows必備)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        #【設定初始化，UI標題與視窗大小】
        self.setWindowTitle('自動排程系統 ver 1.1')
        self.setWindowIcon(QIcon('favicon.ico'))
        self.resize(QSize(1500, 900))

        #【新增UI中的顯示元件】
        # ● 按鍵
        self.btn_upload_workbill_csv = QPushButton('載入訂單資料')
        self.btn_upload_machine_csv = QPushButton('載入機台資料')
        self.btn_upload_priority_csv = QPushButton('載入順位資料')
        self.btn_upload_mold_csv = QPushButton('載入模具資料')
        self.btn_start = QPushButton('開始排程')
        self.btn_set_flag = QPushButton('確定旗標時間')
        self.btn_restart = QPushButton('更改後重新排程')
        self.btn_download_result_csv = QPushButton('下載排程後訂單')
        # ● 字元 (一開始如不設定內容，初始可空白)
        self.label_maintitle = QLabel('自動排程系統')
        self.label_upload_workbill_filename = QLabel()
        self.label_upload_machine_filename = QLabel()
        self.label_upload_priority_filename = QLabel()
        self.label_upload_mold_filename = QLabel()
        self.label_cm = QLabel('換料常數 (秒)')
        self.label_cc = QLabel('換色常數 (秒)')
        self.label_alphac = QLabel('換色系數')
        self.label_prior2 = QLabel('第2級加權係數')
        self.label_prior3 = QLabel('第3級加權係數')
        self.label_scheduling_time = QLabel('排程當下時間')
        self.label_time_flag = QLabel('旗標時間')
        self.label_message = QLabel()
        # self.version_number = QLabel('V1.1')

        # ● 輸入欄位 (因之後會放在分頁裡，所以先完成layput)
        self.edit_cm = QLineEdit('2400')
        self.edit_cc = QLineEdit('1200')
        self.edit_alphac = QLineEdit('1.05')
        self.edit_prior2 = QLineEdit('1.2')
        self.edit_prior3 = QLineEdit('1.5')

        # ● 輸入日曆
        self.calendar_date1 = QCalendarWidget()
        self.calendar_date2 = QCalendarWidget()

        # ● 輸入時間
        self.dateEdit = QDateTimeEdit(QDateTime(2020, 11, 30, 8, 0, 0, 0, 0), self)
        # self.dateEdit = QDateTimeEdit(QDateTime.currentDateTime(), self)
        # self.dateEdit_flag = QDateTimeEdit(QDateTime.currentDateTime(), self)
        self.dateEdit_flag = QDateTimeEdit(QDateTime(2020, 12, 4, 8, 0, 0, 0, 0), self)
        
        # ● 樹表格顯示
        self.tree_sepa_job = QTreeWidget()
        self.tree_sepa_job.setColumnCount(2)
        self.tree_sepa_job.setHeaderLabels(['選擇拆單', '拆單數值與新交期']) #['key', 'Value']
        self.tree_sepa_job.setFixedHeight(150)

        # ● 圖片-圖片引擎
        self.plot_output_result = MplWidget()
        self.browser = QWebEngineView(self)
        # ● 分頁
        self.tabs_setting = QTabWidget()  

        ######分頁內容：輸入資料######
        input_data_layout = QVBoxLayout()
        input_data_layout.addWidget(self.btn_upload_workbill_csv)
        input_data_layout.addWidget(self.label_upload_workbill_filename)
        input_data_layout.addWidget(self.btn_upload_machine_csv)
        input_data_layout.addWidget(self.label_upload_machine_filename)
        input_data_layout.addWidget(self.btn_upload_priority_csv)
        input_data_layout.addWidget(self.label_upload_priority_filename)
        input_data_layout.addWidget(self.btn_upload_mold_csv)
        input_data_layout.addWidget(self.label_upload_mold_filename)
        input_data_widget = QWidget()
        input_data_widget.setLayout(input_data_layout)
        #############################
        
        ######分頁內容：參數設定######
        parameter_layout = QVBoxLayout()

        cm_layout = QHBoxLayout() 
        cm_layout.addWidget(self.label_cm)
        cm_layout.addWidget(self.edit_cm)
        cm_layout.setStretchFactor(self.label_cm, 3)   #比例調整
        cm_layout.setStretchFactor(self.edit_cm, 2)    #比例調整
        cm_widget = QWidget()
        cm_widget.setLayout(cm_layout)

        cc_layout = QHBoxLayout() 
        cc_layout.addWidget(self.label_cc)
        cc_layout.addWidget(self.edit_cc)
        cc_layout.setStretchFactor(self.label_cc, 3)   #比例調整
        cc_layout.setStretchFactor(self.edit_cc, 2)    #比例調整
        cc_widget = QWidget()
        cc_widget.setLayout(cc_layout)

        alphac_layout = QHBoxLayout() 
        alphac_layout.addWidget(self.label_alphac)
        alphac_layout.addWidget(self.edit_alphac)
        alphac_layout.setStretchFactor(self.label_alphac, 3)   #比例調整
        alphac_layout.setStretchFactor(self.edit_alphac, 2)    #比例調整
        alphac_widget = QWidget()
        alphac_widget.setLayout(alphac_layout)

        prior2_layout = QHBoxLayout() 
        prior2_layout.addWidget(self.label_prior2)
        prior2_layout.addWidget(self.edit_prior2)
        prior2_layout.setStretchFactor(self.label_prior2, 3)   #比例調整
        prior2_layout.setStretchFactor(self.edit_prior2, 2)    #比例調整
        prior2_widget = QWidget()
        prior2_widget.setLayout(prior2_layout)

        prior3_layout = QHBoxLayout() 
        prior3_layout.addWidget(self.label_prior3)
        prior3_layout.addWidget(self.edit_prior3)
        prior3_layout.setStretchFactor(self.label_prior3, 3)   #比例調整
        prior3_layout.setStretchFactor(self.edit_prior3, 2)    #比例調整
        prior3_widget = QWidget()
        prior3_widget.setLayout(prior3_layout)

        parameter_layout.addWidget(cm_widget)
        parameter_layout.addWidget(cc_widget)
        parameter_layout.addWidget(alphac_widget)
        parameter_layout.addWidget(prior2_widget)
        parameter_layout.addWidget(prior3_widget)
        parameter_widget = QWidget()
        parameter_widget.setLayout(parameter_layout)
        #############################

        ######分頁內容：輸入資料######
        first_run_layout = QVBoxLayout()
        first_run_layout.addWidget(self.label_scheduling_time)
        first_run_layout.addWidget(self.dateEdit)
        first_run_layout.addWidget(self.btn_start)
        first_run_widget = QWidget()
        first_run_widget.setLayout(first_run_layout)
        #############################

        ######捲動區域內容：可變動單子######
        rerun_layout = QVBoxLayout()
        rerun_layout.addWidget(self.label_time_flag)
        rerun_layout.addWidget(self.dateEdit_flag)
        rerun_layout.addWidget(self.btn_set_flag)
        rerun_layout.addWidget(self.tree_sepa_job)
        rerun_layout.addWidget(self.btn_restart)
        rerun_widget = QWidget()
        rerun_widget.setLayout(rerun_layout)
        #############################

        # ● 捲動區域
        ## 設定捲動區域
        self.scroll_input_data = QScrollArea() # 建立捲動區域，並將scroll_widget設置其中
        self.scroll_input_data.setWidgetResizable(True)  # 設置是否自動調整部件大小(必須要True)
        self.scroll_input_data.setWidget(input_data_widget)

        self.scroll_parameter = QScrollArea()
        self.scroll_parameter.setWidgetResizable(True)
        self.scroll_parameter.setWidget(parameter_widget)

        self.scroll_first_run = QScrollArea()
        self.scroll_first_run.setWidgetResizable(True)
        self.scroll_first_run.setWidget(first_run_widget)

        self.scroll_rerun = QScrollArea()
        self.scroll_rerun.setWidgetResizable(True)
        self.scroll_rerun.setWidget(rerun_widget)
        self.scroll_rerun.setFixedHeight(300)

        #【設定元件】
        ### ● 字型
        self.label_maintitle.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 15pt; font-weight: bold;}')
        self.label_upload_workbill_filename.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 8pt; border: 1px solid black;}')
        self.label_upload_machine_filename.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 8pt; border: 1px solid black;}')
        self.label_upload_priority_filename.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 8pt; border: 1px solid black;}')
        self.label_upload_mold_filename.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 8pt; border: 1px solid black;}')
        self.label_cm.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 9pt;}')
        self.label_cc.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 9pt;}')
        self.label_alphac.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 9pt;}')
        self.label_prior2.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 9pt;}')
        self.label_prior3.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 9pt;}')
        self.label_scheduling_time.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 10pt; font-weight: bold;}')
        self.label_time_flag.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 10pt; font-weight: bold;}')
        self.label_message.setStyleSheet('QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 10pt; border: 1px solid black;}')
        self.label_upload_workbill_filename.setWordWrap(True) # 自動換行
        self.label_upload_machine_filename.setWordWrap(True)
        self.label_upload_priority_filename.setWordWrap(True)
        self.label_upload_mold_filename.setWordWrap(True)
        self.label_message.setWordWrap(True)
        self.label_maintitle.setFixedHeight(30)  # 固定高度
        self.label_upload_workbill_filename.setFixedHeight(60)
        self.label_upload_machine_filename.setFixedHeight(60)
        self.label_upload_priority_filename.setFixedHeight(60)
        self.label_upload_mold_filename.setFixedHeight(60)
        self.label_scheduling_time.setFixedHeight(40)
        self.label_time_flag.setFixedHeight(40)


        ### ● 選單區域文字
        ### ● 按鍵字元
        self.btn_upload_workbill_csv.setStyleSheet('QPushButton{font-family: Microsoft JhengHei; font-size: 10pt;}')
        self.btn_upload_machine_csv.setStyleSheet('QPushButton{font-family: Microsoft JhengHei; font-size: 10pt;}')
        self.btn_upload_priority_csv.setStyleSheet('QPushButton{font-family: Microsoft JhengHei; font-size: 10pt;}')
        self.btn_upload_mold_csv.setStyleSheet('QPushButton{font-family: Microsoft JhengHei; font-size: 10pt;}')
        self.btn_start.setStyleSheet('QPushButton{font-family: Microsoft JhengHei; font-size: 10pt;}')
        self.btn_set_flag.setStyleSheet('QPushButton{font-family: Microsoft JhengHei; font-size: 10pt;}')
        self.btn_restart.setStyleSheet('QPushButton{font-family: Microsoft JhengHei; font-size: 10pt;}')
        self.btn_download_result_csv.setStyleSheet('QPushButton{font-family: Microsoft JhengHei; font-size: 10pt;}')
        self.btn_upload_workbill_csv.setCursor(QCursor(QtCore.Qt.PointingHandCursor)) # 游標移過去時會變成手指
        self.btn_upload_machine_csv.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_upload_priority_csv.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_upload_mold_csv.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_start.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_set_flag.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_restart.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_download_result_csv.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        ### ● 輸入時間
        self.dateEdit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.dateEdit_flag.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.dateEdit.setCalendarPopup(True) # 彈出日曆
        self.dateEdit_flag.setCalendarPopup(True)
        self.dateEdit.setStyleSheet('QDateTimeEdit{font-family: Microsoft JhengHei}')
        self.dateEdit_flag.setStyleSheet('QDateTimeEdit{font-family: Microsoft JhengHei}')
        self.dateEdit.setCalendarWidget(self.calendar_date1)  
        self.dateEdit_flag.setCalendarWidget(self.calendar_date2)  
        ### ● 日曆
        self.calendar_date1.setStyleSheet("QCalendarWidget{font-family: Microsoft JhengHei;}")
        self.calendar_date2.setStyleSheet("QCalendarWidget{font-family: Microsoft JhengHei;}")
        self.calendar_date1.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.calendar_date2.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.calendar_date1.setGridVisible(True) # 決定是否顯示格線
        self.calendar_date2.setGridVisible(True)
        ### ● 輸入欄位
        self.edit_cm.setStyleSheet('QLineEdit{font-family: Microsoft JhengHei;}')
        self.edit_cc.setStyleSheet('QLineEdit{font-family: Microsoft JhengHei;}')
        self.edit_alphac.setStyleSheet('QLineEdit{font-family: Microsoft JhengHei;}')
        self.edit_prior2.setStyleSheet('QLineEdit{font-family: Microsoft JhengHei;}')
        self.edit_prior3.setStyleSheet('QLineEdit{font-family: Microsoft JhengHei;}')
        self.edit_cm.setValidator(QIntValidator())  # 設定限定輸入字元形式，如整數Int、浮點數Double
        self.edit_cc.setValidator(QIntValidator())
        self.edit_alphac.setValidator(QDoubleValidator())
        self.edit_prior2.setValidator(QDoubleValidator())
        self.edit_prior3.setValidator(QDoubleValidator())
        ### ● 分頁 (先分配各分頁區塊)
        self.tabs_setting.addTab(self.scroll_input_data, '輸入資料')
        self.tabs_setting.addTab(self.scroll_parameter, '參數設定')
        self.tabs_setting.addTab(self.scroll_first_run, '初次排程')
        
        self.tabs_setting.setFixedHeight(260)
        self.tabs_setting.setStyleSheet('QTabWidget{font-family: Microsoft JhengHei; font-size: 9pt;}')

        #【設定佈局(layout)】
        # main layout
        main_layout = QHBoxLayout()   # 建立layout，最初指定垂直切分。layout之後要定義一個widget讓layout設定進去(註*1)
        #################################
        #### left layout ####
        left_layout = QVBoxLayout() 

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.label_maintitle)  # 建立layout之後就可以塞元件了
        left_layout.addWidget(self.tabs_setting)
        left_layout.addWidget(self.scroll_rerun)
        left_layout.addWidget(self.btn_download_result_csv)
        left_layout.addWidget(self.label_message)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        #### right layout ####
        right_layout = QHBoxLayout() 
        right_layout.addWidget(self.browser)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        main_layout.setStretchFactor(left_widget, 1) 
        main_layout.setStretchFactor(right_widget, 3)
        #################################
        main_widget = QWidget()                       # (註*1)每一次建layout後要用widget包
        main_widget.setLayout(main_layout)            # (註*1)每一次建layout後要用widget包
        self.setCentralWidget(main_widget)            # 設定main_widget為中心視窗

        #【設定button觸發的slot(function)】
        self.btn_upload_workbill_csv.clicked.connect(self.slot_upload_workbill)
        self.btn_upload_machine_csv.clicked.connect(self.slot_upload_machine)
        self.btn_upload_priority_csv.clicked.connect(self.slot_upload_priority)
        self.btn_upload_mold_csv.clicked.connect(self.slot_upload_mold)
        self.btn_start.clicked.connect(self.slot_start)
        self.btn_set_flag.clicked.connect(self.slot_set_flag)
        self.btn_restart.clicked.connect(self.slot_restart)
        self.btn_download_result_csv.clicked.connect(self.slot_download_result)
        # 【設定全域變數】
        self.workbill_filename = None    # 初次排程的三個輸入檔案名稱
        self.machine_filename = None     
        self.priority_filename = None  
        self.mold_filename = None  
        self.workbill_df = pd.DataFrame() # 初次排程的三個輸入檔案
        self.machine_df = pd.DataFrame()
        self.priority_df = pd.DataFrame()
        self.mold_df = pd.DataFrame()
        self.result_workbill = pd.DataFrame() # 完成初次排程的檔案
        self.gantt_df = pd.DataFrame()        # 同上
        self.dsl = None                       # 同上
        self.date = None  # 初次排程時間
        self.th1_work = None
        self.th2_work = None
        self.date_flag = None # 二次排程時間
        self.time_flag = 0 # 為二次排程時間扣除初次排程時間的秒數
        self.current_job_list = [] 
        self.drop_job_list = []

    def slot_upload_workbill(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'Data Files (*.csv)')  # 建立對話盒(dialog)
        if file:
            self.workbill_filename = file
            self.label_upload_workbill_filename.setText(file) # 複寫label文字為檔名(file)
    
    def slot_upload_machine(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'Data Files (*.csv)')
        if file:
            self.machine_filename = file
            self.label_upload_machine_filename.setText(file)
    
    def slot_upload_priority(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'Data Files (*.csv)')
        if file:
            self.priority_filename = file
            self.label_upload_priority_filename.setText(file)

    def slot_upload_mold(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'Data Files (*.csv)')
        if file:
            self.mold_filename = file
            self.label_upload_mold_filename.setText(file)

    def slot_start(self):
        # 初次排程時的甘特圖資料與時間都需要重置
        self.gantt_df = pd.DataFrame()
        self.date = self.dateEdit.dateTime().toString('yyyy-MM-dd hh:mm:ss')
        if (self.workbill_filename == None) | (self.machine_filename == None) | (self.priority_filename == None):
            self.label_message.setText('請確認是否已載入檔案')
        elif (len(self.edit_cm.text()) * len(self.edit_cc.text()) * len(self.edit_alphac.text()) * len(self.edit_prior2.text()) * len(self.edit_prior3.text())) == 0:
            self.label_message.setText('請確認參數是否確實設定')
        elif ((float(self.edit_cm.text()) < 0) | (float(self.edit_cc.text()) < 0) | (float(self.edit_alphac.text()) < 0) | (float(self.edit_prior2.text()) < 0) | (float(self.edit_prior3.text()) < 0)):
            self.label_message.setText('請確認參數是否超出範圍')
        else:
            try:
                self.workbill_df = pd.read_csv(self.workbill_filename)
                self.machine_df = pd.read_csv(self.machine_filename)
                self.priority_df = pd.read_csv(self.priority_filename)
                self.mold_df = pd.read_csv(self.mold_filename)
            except:
                self.label_message.setText('請確認檔案格式')
            else:
                self.label_message.setText('計算中...')
                parameter_list = [int(self.edit_cm.text()), int(self.edit_cc.text()), float(self.edit_alphac.text()), float(self.edit_prior2.text()), float(self.edit_prior3.text())]
                self.th1_work = WorkThread(self.date, self.workbill_df, self.machine_df, self.priority_df, self.mold_df, self.gantt_df, parameter_list)
                self.th1_work.start()
                self.th1_work.signal_action.connect(self.slot_message)
                self.th1_work.signal_df_result.connect(self.slot_save_result_df)
                self.th1_work.signal_df_gantt.connect(self.slot_save_gantt_df)
                self.th1_work.signal_fig_gantt.connect(self.slot_draw_gantt_df)
                self.th1_work.signal_list_dsl.connect(self.slot_check_schedule_list)
        self.btn_restart.setEnabled(True)

    def slot_set_flag(self):
        # 依照旗標時間重新顯示每台機台正在做的訂單資訊(樹表格)
        self.current_job_list, self.drop_job_list = [], []
        
        if (self.date == None) | (len(self.result_workbill) <= 0): 
            self.label_message.setText('請先做初次排程')
        else:
            self.tree_sepa_job.clear()  # 重置樹表格
            self.date_flag = self.dateEdit_flag.dateTime().toString('yyyy-MM-dd hh:mm:ss')
            self.time_flag = (datetime.strptime(self.date_flag, '%Y-%m-%d %H:%M:%S') - datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')).total_seconds()
            for ds in self.dsl:
                info_dict, current_job, done_job_list = {}, None, []
                Ct_list, Job_list = ds['c_time'], ds['Job']
                for index, c_t in enumerate(Ct_list):
                    if (index == 0) & (self.time_flag < c_t):  # 排單後還沒有單子正在生產
                        current_job, done_job_list = None, []
                    elif (index == len(Ct_list) - 1) & (c_t <= self.time_flag): # 單子都排完了
                        current_job, done_job_list = None, Job_list
                    elif (Ct_list[index - 1] <= self.time_flag) & (self.time_flag < c_t): # 可以記錄當下安排哪張單
                        current_job, done_job_list = Job_list[index], Job_list[1 : index]
                info_dict['machineNo'], info_dict['Job'] = ds['machineNo'], current_job ####
                self.current_job_list.append(info_dict)
                self.drop_job_list += done_job_list
        
            for device_job in self.current_job_list:
                # Create top root.
                root = QTreeWidgetItem(self.tree_sepa_job)
                root.setText(0, '{}-{}'.format(device_job['machineNo'], device_job['Job']))
                root.setCheckState(0, Qt.Unchecked)
                
                # Create child (數值部分依單而定)
                child_num = QTreeWidgetItem()
                child_num.setText(0, '數量')
                
                child_endtime = QTreeWidgetItem()
                child_endtime.setText(0, 'EndTime')

                if (device_job['Job'] == None):
                    str_num, str_endtime = None, None
                else:
                    str_num = self.workbill_df[self.workbill_df['billNo'] == device_job['Job']]['qty'].values[0]
                    str_endtime = self.workbill_df[self.workbill_df['billNo'] == device_job['Job']]['endTime'].dt.strftime('%Y-%m-%d %H:%M:%S').values[0]
                child_num.setText(1, '{}'.format(str_num))
                child_endtime.setText(1, '{}'.format(str_endtime))

                # Add child to root.
                root.addChild(child_num)
                root.addChild(child_endtime)

                # Set editable.
                self.tree_sepa_job.openPersistentEditor(child_num, 1)
                self.tree_sepa_job.openPersistentEditor(child_endtime, 1)
    
    def slot_restart(self):
        # 再次排程需要
        if (self.date == None) | (self.date_flag == None):
            self.label_message.setText('請先做初次排程與二次排程')
        else:
            self.machine_df = pd.read_csv(self.machine_filename)
            self.priority_df = pd.read_csv(self.priority_filename)
            self.workbill_df = pd.read_csv(self.workbill_filename)
            self.mold_df = pd.read_csv(self.mold_filename)
            cut_job_list = []
            for i in range(len(self.current_job_list)):
                if (self.tree_sepa_job.topLevelItem(i).checkState(0) == Qt.Checked): # 有打勾
                    try:
                        new_size = int(self.tree_sepa_job.topLevelItem(i).child(0).text(1))
                        new_end_time = datetime.strptime(self.tree_sepa_job.topLevelItem(i).child(1).text(1), '%Y-%m-%d %H:%M:%S')
                    except:
                        self.label_message.setText('拆單輸入數值格式錯誤')
                    else:   # 打勾的都確認完，開始處理輸入資料
                        cut_job_list.append(str(self.current_job_list[i]['Job']))
                        # 【machine_df】
                        self.machine_df.loc[i, ['colorNo', 'materialNo']] = \
                            self.result_workbill[self.result_workbill['billNo'] == self.current_job_list[i]['Job']][['colorNo', 'materialNo']].values.tolist()[0]
                        self.machine_df.loc[i, 'start_working_date'] = self.date_flag

                        # 【priority_df】
                        for col in self.priority_df.columns[1:]:
                            target = self.priority_df.loc[self.priority_df['productNo'] == self.result_workbill[self.result_workbill['billNo'] == self.current_job_list[i]['Job']]['productNo'].values.tolist()[0], col].values[0]
                            if target == target:
                                if self.current_job_list[i]['machineNo'] in target:
                                    new_selection_str = ''
                                    for device in [device for device in target.split(',') if device != self.current_job_list[i]['machineNo']]:
                                        if len(new_selection_str) == 0: new_selection_str += device
                                        else: new_selection_str += (',' + device)
                                    self.priority_df.loc[self.priority_df['productNo'] == self.result_workbill[self.result_workbill['billNo'] == self.current_job_list[i]['Job']]['productNo'].values.tolist()[0], col] = new_selection_str
                                    break
                        
                        # 【workbill_df】 複製拆分前的單，並此單修改此單
                        self.workbill_df.loc[len(self.workbill_df)] = self.workbill_df.loc[self.workbill_df['billNo'] == self.current_job_list[i]['Job']].values.tolist()[0]
                        self.workbill_df.loc[len(self.workbill_df) - 1, ['billNo', 'qty', 'endTime']] = ['{}_sub'.format(self.current_job_list[i]['Job']), new_size, new_end_time]

                
                if ((self.tree_sepa_job.topLevelItem(i).checkState(0) == Qt.Unchecked) & (self.current_job_list[i]['Job'] != None)): # 沒打勾
                    # 【machine_df】
                    self.machine_df.loc[i, ['colorNo', 'materialNo', 'start_working_date']] = \
                        self.result_workbill[self.result_workbill['billNo'] == self.current_job_list[i]['Job']][['colorNo', 'materialNo', 'c_time']].values.tolist()[0]
                
            # 【workbill_df】 拿掉已經生產的單(self.current_job_list與self.drop_job_list)
            drop_list = [i['Job'] for i in self.current_job_list] + self.drop_job_list 
            for machine_job in self.current_job_list: drop_list.append(machine_job['Job'])
            self.workbill_df = self.workbill_df[~self.workbill_df['billNo'].isin(drop_list)]
            self.workbill_df.reset_index(drop = True, inplace = True)
            self.gantt_df = self.gantt_df[self.gantt_df['billNo'].isin([str(i) for i in drop_list])]   ########原本已經排好的甘特圖資料
            self.gantt_df.reset_index(drop = True, inplace = True)
            for i in range(len(self.gantt_df)):
                if (self.gantt_df.loc[i, 'billNo'] in cut_job_list):
                    self.gantt_df.loc[i, 'Complete'] = self.date_flag
            self.gantt_df.loc[:, 'Complete'] = pd.to_datetime(self.gantt_df.loc[:, 'Complete'])

            parameter_list = [int(self.edit_cm.text()), int(self.edit_cc.text()), float(self.edit_alphac.text()), float(self.edit_prior2.text()), float(self.edit_prior3.text())]
            self.th2_work = WorkThread(self.date_flag, self.workbill_df, self.machine_df, self.priority_df, self.mold_df, self.gantt_df, parameter_list)
            self.th2_work.start()
            self.th2_work.signal_action.connect(self.slot_message)
            self.th2_work.signal_df_result.connect(self.slot_save_result_df)
            self.th2_work.signal_df_gantt.connect(self.slot_save_gantt_df)
            self.th2_work.signal_fig_gantt.connect(self.slot_draw_gantt_df)
            self.th2_work.signal_list_dsl.connect(self.slot_check_schedule_list)
            self.btn_restart.setEnabled(False)

    def slot_message(self, message_str):
        self.label_message.setText(message_str) 
    
    def slot_save_result_df(self, data_df):
        self.result_workbill = data_df
    
    def slot_save_gantt_df(self, data_df):
        self.gantt_df = data_df

    def slot_draw_gantt_df(self, object):
        self.browser.setHtml(object.to_html(include_plotlyjs = 'cdn'))

    def slot_download_result(self):
        if len(self.result_workbill) <= 0:
            self.label_message.setText('尚未有排程結果！請確認是否已載入資料並執行。')
        else:
            fileName, _ = QFileDialog.getSaveFileName(self, 'Save file', '', '*.csv')  # 建立儲存檔案的對話盒(dialog)
            if fileName:
                self.result_workbill.to_csv(fileName, index = None)
    
    def slot_check_schedule_list(self, dsl_list):
        self.dsl = dsl_list

def main():
    app = QApplication([])
    app.setStyle(QStyleFactory.create('fusion'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

