import datetime
import json
import urllib
import pandas as pd
import numpy as np
import requests
import pygsheets
import io
from collections import Counter
import datetime
import schedule
import time
from pandas import read_excel
import base64
from django.core.files.base import ContentFile
# from datetime import datetime
from calendar import monthrange

def last_day_of_month(date_value):
    return date_value.replace(day=monthrange(date_value.year, date_value.month)[1])


def read_main_file():
    scope = ['https://spreadsheets.google.com/feeds']
    gc = pygsheets.authorize(service_file='C:/Users/patel.vaishakhi/Downloads/fourth-stock-291709-1cadc070c80b.json')
    emp_master = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/1soEWcz-KwUAUR_8ua3xTHDHr0dfR5QEce4-gI0lnPyI/edit#gid=0')
    wks3 = emp_master.worksheet_by_title("EmployeeMaster")
    EmployeeMaster = wks3.get_as_df()
    # EmployeeMaster = read_excel(
    #     'C:/Users/patel.vaishakhi/Downloads/EmployeeMaster.xlsx')
    for index, row in EmployeeMaster.iterrows():
        if row["LWD"] == "":
            EmployeeMaster.at[index, "LWD"] = '31-Dec-2200'
    EmployeeMaster['DATE OF JOINING (DD/MM/YY)'] = pd.to_datetime(
        EmployeeMaster['DATE OF JOINING (DD/MM/YY)']).dt.strftime('%Y-%m-%d')
    EmployeeMaster.insert(5, "LWD_Remarks", EmployeeMaster['LWD'], True)
    EmployeeMaster['LWD'] = EmployeeMaster['LWD'].astype(str).str.replace(
        "To be confirmed|Temporary Suspension|Data received from payroll team|to be cofirmed|Not Joined|to be confirmed|not joined|LWD is not available|Layoff cases|Absconded|LWd not available",
        '31-Dec-2200', regex=True, case=False)
    EmployeeMaster['LWD'] = pd.to_datetime(
        EmployeeMaster['LWD']).dt.strftime('%Y-%m-%d')
    EmployeeMaster.rename(columns={'DEPARTMENT': 'Department', 'FUNCTION /CATEGORY ': 'Function_Category',
                                   'TEAM': 'Team', 'SUB TEAM': 'Sub_team', 'STATE': 'State', 'CITY': 'City',
                                   'DATE OF JOINING (DD/MM/YY)': 'DOJ',
                                   'LOCATION': 'Location', 'VENDOR NAME': 'VendorName'}, inplace=True)
    EmployeeMaster = EmployeeMaster.applymap(
        lambda s: s.lower() if type(s) == str else s)
    return EmployeeMaster


def return_frequency(filter_dict):
    for key in filter_dict:
        if key == "frequency":
            if len(list(filter_dict[key])) > 0:
                return list(filter_dict[key])[0]
            else:
                return "Monthly"


def return_date_list(frequency,filter_dict):
    from datetime import date
    from datetime import timedelta 
    date_value_list=[]
    today = date.today()
    if frequency=="Yesterday":
        yesterday = today - timedelta(days = 1)
        date_value_list.append(yesterday.strftime('%Y-%m-%d'))
    elif frequency=="Week":
        today = date.today().strftime('%Y-%m-%d')
        dates = [datetime.datetime.strptime(today, '%Y-%m-%d') - datetime.timedelta(days=i) for i in range(7)]
        for day in dates:
            date_value_list.append(day.strftime('%Y-%m-%d').upper())
    elif frequency=="Fifteen":
        today = date.today().strftime('%Y-%m-%d')
        dates = [datetime.datetime.strptime(today, '%Y-%m-%d') - datetime.timedelta(days=i) for i in range(15)]
        for day in dates:
            date_value_list.append(day.strftime('%Y-%m-%d').upper())
    elif frequency=="MTD":
        today = date.today().strftime('%Y-%m-%d')
        dates= pd.date_range('2020-01-01',today , freq='1M')-pd.offsets.MonthBegin(1)
        date_value_list=dates.strftime("%Y-%m-%d").tolist()
    elif frequency=="Quarterly YTD":
        # import datetime
        quarter_list=[("Q1",[1,4]),
             ("Q2",[4,7]),
             ("Q3",[7,10]),
             ("Q4",[10,12])]
        quarter_start=""
        for key in filter_dict:
                if key=="end_date":
                    if type(filter_dict[key])==list:
                        end_date=filter_dict[key][0]
                        datee = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                        for quarter in quarter_list:
                            if int(datee.month) >= int(quarter[1][0]) and int(datee.month) < int(quarter[1][1]):
                                quarter_start=quarter[0]
                                first_day = datetime.date(datee.year, quarter[1][0], 1)
                                last_day=datetime.date(datee.year, quarter[1][1], 1)
                                date_value_list.append([first_day.strftime('%Y-%m-%d'),last_day.strftime('%Y-%m-%d')])
                            
                        for quarter in quarter_list:
                            if len(date_value_list)<=7:
                                    prev=datee.year
                                    first_day = datetime.date(prev, quarter[1][0], 1)
                                    last_day=datetime.date(prev, quarter[1][1], 1)
                                    if [first_day.strftime('%Y-%m-%d'),last_day.strftime('%Y-%m-%d')] not in date_value_list:
                                        if datee.date()>first_day:
                                            date_value_list.append([first_day.strftime('%Y-%m-%d'),last_day.strftime('%Y-%m-%d')])
 
                        for quarter in quarter_list:
                            if len(date_value_list)<=7:
                                    prev=datee.year-1
                                    first_day = datetime.date(prev, quarter[1][0], 1)
                                    last_day=datetime.date(prev, quarter[1][1], 1)
                                    date_value_list.append([first_day.strftime('%Y-%m-%d'),last_day.strftime('%Y-%m-%d')])
                        
                        for quarter in quarter_list:
                            if len(date_value_list)<=7:
                                    prev=datee.year-2
                                    first_day = datetime.date(prev, quarter[1][0], 1)
                                    last_day=datetime.date(prev, quarter[1][1], 1)
                                    date_value_list.append([first_day.strftime('%Y-%m-%d'),last_day.strftime('%Y-%m-%d')])
                        

    return date_value_list


def return_final_table(EmployeeMaster,date_value_list,report_type,frequency):
    from datetime import datetime
    lst = EmployeeMaster['VendorName'].unique().tolist()
    final_dataframe = pd.DataFrame(lst,columns =['VendorName']) 
    final_dataframe = final_dataframe.reindex(columns = final_dataframe.columns.tolist()) 
#     date_value_list.reverse()
    if report_type=="Monthly HC":
        if frequency=="MTD":
            for date_value in date_value_list:
                    given_date = datetime(year=2020, month=int(date_value.split('-')[1]), day=1).date()
                    end_of_month=last_day_of_month(given_date)
                    end_of_month=pd.to_datetime(end_of_month).strftime('%Y-%m-%d')
                    filtered_df=EmployeeMaster[(EmployeeMaster['DOJ']<=end_of_month) & (EmployeeMaster['LWD']>=date_value)]
                    print(date_value)
                    for index,row in final_dataframe.iterrows():
                        count=0
                        filter_dict_vendor={"VendorName":row["VendorName"]}
                        for key in filter_dict_vendor:
                            count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                        final_dataframe.at[index,date_value]=count
    elif report_type=="Opening HC":
        if frequency!="Quarterly YTD":
            for date_value in date_value_list:
                        given_date = datetime(year=2020, month=int(date_value.split('-')[1]), day=1).date()
                        end_of_month=last_day_of_month(given_date)
                        end_of_month=pd.to_datetime(end_of_month).strftime('%Y-%m-%d')
                        filtered_df=EmployeeMaster[(EmployeeMaster['DOJ']<=date_value) & (EmployeeMaster['LWD']>=date_value)]
                        print(date_value)
                        for index,row in final_dataframe.iterrows():
                            count=0
                            filter_dict_vendor={"VendorName":row["VendorName"]}
                            for key in filter_dict_vendor:
                                count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                            final_dataframe.at[index,date_value]=count
        else:
             for date_value in date_value_list:
                        given_date = datetime(year=2020, month=int(date_value[0].split('-')[1]), day=1).date()
                        end_of_month=pd.to_datetime(date_value[1]).strftime('%Y-%m-%d')
                        filtered_df=EmployeeMaster[(EmployeeMaster['DOJ']<=date_value[0]) & (EmployeeMaster['LWD']>=date_value[0])]
                        print(date_value)
                        for index,row in final_dataframe.iterrows():
                            count=0
                            filter_dict_vendor={"VendorName":row["VendorName"]}
                            for key in filter_dict_vendor:
                                count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                            final_dataframe.at[index,date_value[0]]=count              
    elif report_type=="Closing HC":
        if frequency!="Quarterly YTD":
            for date_value in date_value_list:
                        given_date = datetime(year=2020, month=int(date_value.split('-')[1]), day=1).date()
                        end_of_month=last_day_of_month(given_date)
                        end_of_month=pd.to_datetime(end_of_month).strftime('%Y-%m-%d')
                        filtered_df=EmployeeMaster[(EmployeeMaster['DOJ']<=end_of_month) & (EmployeeMaster['LWD']>=end_of_month)]
                        
                        for index,row in final_dataframe.iterrows():
                            count=0
                            filter_dict_vendor={"VendorName":row["VendorName"]}
                            for key in filter_dict_vendor:
                                count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                            final_dataframe.at[index,date_value]=count
        else:
            for date_value in date_value_list:
                given_date = datetime(year=2020, month=int(date_value[0].split('-')[1]), day=1).date()
                end_of_month=pd.to_datetime(date_value[1]).strftime('%Y-%m-%d')
                filtered_df=EmployeeMaster[(EmployeeMaster['DOJ']<=end_of_month) & (EmployeeMaster['LWD']>=end_of_month)]
                
                for index,row in final_dataframe.iterrows():
                    count=0
                    filter_dict_vendor={"VendorName":row["VendorName"]}
                    for key in filter_dict_vendor:
                        count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                    final_dataframe.at[index,date_value[0]]=count

                        
    elif report_type=="Addition":
        if frequency=="Quarterly YTD":
            for date_value in date_value_list:
                    given_date = datetime(year=2020, month=int(date_value[0].split('-')[1]), day=1).date()
                    end_of_month=pd.to_datetime(date_value[1]).strftime('%Y-%m-%d')
                    filtered_df=EmployeeMaster[(EmployeeMaster['DOJ']>=date_value[0]) & (EmployeeMaster['DOJ']<=end_of_month)]
                    for index,row in final_dataframe.iterrows():
                        count=0
                        filter_dict_vendor={"VendorName":row["VendorName"]}
                        for key in filter_dict_vendor:
                            count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                        final_dataframe.at[index,date_value[0]]=count
        else:
            for date_value in date_value_list:
                    given_date = datetime(year=2020, month=int(date_value.split('-')[1]), day=1).date()
                    end_of_month=last_day_of_month(given_date)
                    end_of_month=pd.to_datetime(end_of_month).strftime('%Y-%m-%d')
                    filtered_df=EmployeeMaster[(EmployeeMaster['DOJ']>=date_value) & (EmployeeMaster['DOJ']<=end_of_month)]
                    for index,row in final_dataframe.iterrows():
                        count=0
                        filter_dict_vendor={"VendorName":row["VendorName"]}
                        for key in filter_dict_vendor:
                            count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                        final_dataframe.at[index,date_value]=count

    elif report_type=="Exit":
        if frequency!="Quarterly YTD":
            for date_value in date_value_list:
                        given_date = datetime(year=2020, month=int(date_value.split('-')[1]), day=1).date()
                        end_of_month=last_day_of_month(given_date)
                        end_of_month=pd.to_datetime(end_of_month).strftime('%Y-%m-%d')
                        filtered_df=EmployeeMaster[(EmployeeMaster['LWD']>=date_value) & (EmployeeMaster['LWD']<=end_of_month)]
                        
                        for index,row in final_dataframe.iterrows():
                            count=0
                            filter_dict_vendor={"VendorName":row["VendorName"]}
                            for key in filter_dict_vendor:
                                count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                            final_dataframe.at[index,date_value]=count
        else:
            for date_value in date_value_list:
                        given_date = datetime(year=2020, month=int(date_value[0].split('-')[1]), day=1).date()
                        # end_of_month=last_day_of_month(given_date)
                        end_of_month=pd.to_datetime(date_value[1]).strftime('%Y-%m-%d')
                        filtered_df=EmployeeMaster[(EmployeeMaster['LWD']>=date_value[0]) & (EmployeeMaster['LWD']<=end_of_month)]
                        
                        for index,row in final_dataframe.iterrows():
                            count=0
                            filter_dict_vendor={"VendorName":row["VendorName"]}
                            for key in filter_dict_vendor:
                                count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                            final_dataframe.at[index,date_value[0]]=count

    elif report_type=="Attrition rate":
        if frequency!="Quarterly YTD":
            for date_value in date_value_list:
                        given_date = datetime(year=2020, month=int(date_value.split('-')[1]), day=1).date()
                        end_of_month=last_day_of_month(given_date)
                        end_of_month=pd.to_datetime(end_of_month).strftime('%Y-%m-%d')
                        exit_count=len(EmployeeMaster[(EmployeeMaster['LWD']>=date_value) & (EmployeeMaster['LWD']<=end_of_month)])
                        opening_count=len(EmployeeMaster[(EmployeeMaster['DOJ']<=date_value) & (EmployeeMaster['LWD']>=date_value)])
                        closing_count=len(EmployeeMaster[(EmployeeMaster['DOJ']<=end_of_month) & (EmployeeMaster['LWD']>=end_of_month)])
                        
                        for index,row in final_dataframe.iterrows():
                            count=0
                            filter_dict_vendor={"VendorName":row["VendorName"]}
                            filtered_df = pd.DataFrame()
                            for key in filter_dict_vendor:
                                filtered_df=EmployeeMaster[EmployeeMaster[key]==filter_dict_vendor[key]]
                                exit_count=len(filtered_df[(filtered_df['LWD']>=date_value) & (filtered_df['LWD']<=end_of_month)])
                                opening_count=len(filtered_df[(filtered_df['DOJ']<=date_value) & (filtered_df['LWD']>=date_value)])
                                closing_count=len(filtered_df[(filtered_df['DOJ']<=end_of_month) & (filtered_df['LWD']>=end_of_month)])
                                try:
                                    attrition=(exit_count/((opening_count+closing_count)/2))
                                    
                                except:
                                    attrition=0
                                count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                            final_dataframe.at[index,date_value]="{:.0%}".format(attrition)
        else:
            for date_value in date_value_list:
                        given_date = datetime(year=2020, month=int(date_value[0].split('-')[1]), day=1).date()
                        
                        end_of_month=pd.to_datetime(date_value[1]).strftime('%Y-%m-%d')
                        # exit_count=len(EmployeeMaster[(EmployeeMaster['LWD']>=date_value[0]) & (EmployeeMaster['LWD']<=end_of_month)])
                        # opening_count=len(EmployeeMaster[(EmployeeMaster['DOJ']<=date_value[0]) & (EmployeeMaster['LWD']>=date_value[0])])
                        # closing_count=len(EmployeeMaster[(EmployeeMaster['DOJ']<=end_of_month) & (EmployeeMaster['LWD']>=end_of_month)])
                        
                        for index,row in final_dataframe.iterrows():
                            count=0
                            filter_dict_vendor={"VendorName":row["VendorName"]}
                            filtered_df = pd.DataFrame()
                            for key in filter_dict_vendor:
                                filtered_df=EmployeeMaster[EmployeeMaster[key]==filter_dict_vendor[key]]
                                exit_count=len(filtered_df[(filtered_df['LWD']>=date_value[0]) & (filtered_df['LWD']<=end_of_month)])
                                opening_count=len(filtered_df[(filtered_df['DOJ']<=date_value[0]) & (filtered_df['LWD']>=date_value[0])])
                                closing_count=len(filtered_df[(filtered_df['DOJ']<=end_of_month) & (filtered_df['LWD']>=end_of_month)])
                                try:
                                    attrition=(exit_count/((opening_count+closing_count)/2))
                                    
                                except:
                                    attrition=0
                                count=len(filtered_df[filtered_df[key]==filter_dict_vendor[key]])
                            final_dataframe.at[index,date_value[0]]="{:.0%}".format(attrition)
    
         
    
    return final_dataframe

def return_report_type(filter_dict):
    for key in filter_dict:
        if key == "report type":
            print("yes")
            if len(list(filter_dict[key])) > 0:
                return list(filter_dict[key])[0]
            else:
                return "Monthly HC"


def filtered_dataframe(EmployeeMaster, filter_dict):
    for key in filter_dict:
        if key == "dimensions":
            if type(filter_dict[key]) == list:
                for dimensions in filter_dict[key]:
                    for dim in eval(dimensions):

                        if type(eval(dimensions)[dim]) == list:
                            for name in eval(dimensions)[dim]:
                                name = name.lower()

                                EmployeeMaster = EmployeeMaster[EmployeeMaster[dim] == name]

    return EmployeeMaster
