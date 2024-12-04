from __future__ import absolute_import
from __future__ import print_function
from datetime import datetime, date, timedelta 
from nsepy import get_history

import pandas as pd
import os

expiry_file = 'foExp.js'
option_file = 'OptionPrice_dump.csv'
vix_file = 'VIX_data.csv'
index = 'NIFTY 50'
index_option = 'NIFTY'
index_lot = 75
start_date = date(2018,9,1)

#sp_nearer = 50
sp_nearer = 100
options_df = None

def refresh_expiry_dates():

    with open(expiry_file,'r') as exp:
        exp_data =  exp.readlines()
        
    exp_data = [i.replace('\n','')[-12:-2:] for i in exp_data if 'var ' not in i if 'vixExpryDt' not in i if 'stkExpryDt' not in i]
    exp_data_formatted = [datetime.strptime(i, '%d-%m-%Y') for i in exp_data]
    #df = pd.DataFrame({'ExpiryDate':exp_data,'ExpiryDateFormatted': exp_data_formatted})    
    df = pd.DataFrame({'ExpiryDateFormatted': exp_data_formatted})    
    #print(df.head())
    df = df.sort_values(['ExpiryDateFormatted'])
    df['ExpiryDate'] = pd.to_datetime(df['ExpiryDateFormatted'], format='%d-%b-%y')
    df.drop(['ExpiryDateFormatted'], axis=1, inplace=True)
    df.to_csv(expiry_file + '.csv',header=True, sep=',', index=False)
    #exp_data = [datetime.strptime(i, '%d-%m-%Y') for i in exp_data]
    #print(exp_data)

def load_expiry_dates():
    index_cutoff_date = date(2019,2,8)
    df = pd.read_csv(expiry_file + '.csv')
    df['ExpiryDate'] = pd.to_datetime(df['ExpiryDate'], format='%Y-%m-%d')
    df['ExpiryMonth'] = df['ExpiryDate'].apply(lambda x: str(x.year) + '-' + str(x.month) )
    
    df1 = df[df['ExpiryDate'] <= pd.Timestamp(index_cutoff_date)]
    df1_grp = df1.groupby(['ExpiryMonth']).last()
    df1_grp = df1_grp[df1_grp.ExpiryDate != '2019-02-07']
    #df1_grp.reset_index(inplace=True,drop=True)
    #df1_grp.drop(['Prev. Close','Change','Open','High','Low', '% Change'], axis=1, inplace=True)
    
    #print(df1_grp.tail())

    df2 = df[df['ExpiryDate'] > pd.Timestamp(index_cutoff_date)]
    df2 = df2[df2.ExpiryDate != '2019-06-21']
    df2 = df2[df2.ExpiryDate != '2019-03-15']
    
    df = df1_grp.append(df2, ignore_index=True, sort=True)
    df.reset_index(inplace=True,drop=True)
    
    #print(df1_grp.tail())
    #print(df2.head())

    df.drop(['ExpiryMonth'], axis=1, inplace=True)
    #print(df.head())
    #print(df.tail())
    df = df[df['ExpiryDate'] >= pd.Timestamp(start_date)]

    return df
    #df['ExpiryMonth'] = df['ExpiryDate'].apply(lambda x: str(x.year) + '-' + str(x.month) )
    #df_grp = df.groupby(['ExpiryMonth']).last()
    
    #print(df.tail())

    
    
    #return df_grp
    



def load_vix():
    df = pd.read_csv(vix_file)
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    df = df[df['Date'] >= pd.Timestamp(start_date)]
    df.drop(['Prev. Close','Change','Open','High','Low', '% Change'], axis=1, inplace=True)
    df.rename(columns={"Close": "Vix"}, inplace=True)
    df['Vix'] = df['Vix'].apply(lambda x: round(x,2))
    return df



def load_option_prices():
    if os.path.exists(option_file):
        df = pd.read_csv(option_file)
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        df['ExpiryDay'] = pd.to_datetime(df['ExpiryDay'], format='%Y-%m-%d')
    else:
        df = pd.DataFrame(columns=['Date', 'Name', 'Type', 'StrikePrice', 'ExpiryDay','Price'])
    return df

def load_index_data(days_window):
    holidays_in_month = 8
    ddays = holidays_in_month + days_window
    ddate = start_date - timedelta(days=ddays)
    #print(ddate,type(ddate))
    df = pd.read_csv(index + '_data.csv')
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    df = df[df['Date'] >= pd.Timestamp(ddate)]
    df.drop(['Turnover (Rs. Cr)','Shares Traded','Open','High','Low'], axis=1, inplace=True)
    return df

def myround(x, base):
    return base * round(x/base)



#
#def price_from_dump(row,opt):
#    if opt == 'PE':
#        strike_price = row['PutStrikePrice']
#    else:
#        strike_price = row['CallStrikePrice']
#    
#    global options_df
#    
#    print('-->',row['Date'],opt,strike_price,row['ExpiryDay'])
#    
#    found_price = options_df.loc[(options_df['Date'] == row['Date']) & (options_df['Name'] == index_option) & (options_df['Type'] == opt) & (options_df['StrikePrice'] == strike_price) & (options_df['ExpiryDay'] == row['ExpiryDay'])]
#    print('Found ',found_price)
#    
#    if not found_price.empty:
#        print(found_price['Price'].values[0])
#        return found_price['Price'].values[0]
#    else:
#        return 0.0
#
#
#


def options_get_history(row, opt):
    if opt == 'PE':
        strike_price = row['PutStrikePrice']
    else:
        strike_price = row['CallStrikePrice']
    
    global options_df
    #print(len(options_df))
    #print(type(row['Date']))
    #found_price = None
    #print('-->',row['Date'],opt,strike_price,row['ExpiryDay'])
    found_price = options_df.loc[(options_df['Date'] == row['Date']) & (options_df['Name'] == index_option) & (options_df['Type'] == opt) & (options_df['StrikePrice'] == strike_price) & (options_df['ExpiryDay'] == row['ExpiryDay'])]
    #print('Found ',found_price)
    #print(found_price.empty)
    try:
        if found_price.empty:
            print('Fetching Price from NSE {0}_{1}_{2}_{3}'.format(row['ExpiryDay'].date(), int(strike_price), opt,row['Date'].date()))
            nifty_opt_puts = get_history(symbol=index_option,
                                         start=row['Date'],
                                         end=row['Date'],
                                         index=True,
                                         option_type=opt,
                                         strike_price=strike_price,
                                         expiry_date=row['ExpiryDay'])      
            
            if len(nifty_opt_puts['Close']):
                temp_dict = {}
                temp_dict[row['Date']] = {'Name'       : index_option, 
                                         'Type'        : opt, 
                                         'StrikePrice' : strike_price,
                                         'ExpiryDay'   : row['ExpiryDay'],
                                         'Price'       : nifty_opt_puts['Close'][0]}
                temp_df = pd.DataFrame.from_dict(temp_dict, orient='index')
                temp_df['Date'] = temp_df.index
                temp_df.reset_index(inplace=True,drop=True)
                #print(temp_df.head())
                options_df = options_df.append(temp_df,ignore_index = True,sort=False)
                temp_df = None
                #print(len(options_df))
                return nifty_opt_puts['Close'][0]
            else:
                print('Could not fetch price')
                return 0.0
        else:
            print('Fetched price from local')
            return found_price['Price'].values[0]
    except Exception as e:
        print(e)

def return_dayname(day):
    day = str(day)
    dayname = {'1': 'Thursday',
               '2': 'Wednesday',
               '3': 'Tuesday',
               '4': 'Monday',
               '5': 'Friday',
               '6': 'Thursday-1',
               '30': 'Month'}
    return dayname[day]

    
    





def buy_vertical(days_window):
    refresh_expiry_dates()
    expdt_df = load_expiry_dates()
    
    expdt_df = expdt_df[expdt_df.ExpiryDate != '2019-06-21']
    expdt_df = expdt_df[expdt_df.ExpiryDate != '2019-03-15']

    expdt_df.reset_index(inplace=True, drop=True)
    #print(expdt_df.head())
    #print(expdt_df.count())

    index_df = load_index_data(days_window)
    index_df.reset_index(inplace=True,drop=True)
    #print(index_df.head())

    vix_df = load_vix()
    vix_df.reset_index(inplace=True,drop=True)
    #print(vix_df.head())
    
    global options_df
    
    options_df = load_option_prices()
    index_df.reset_index(inplace=True,drop=True)
    
    index_df = pd.merge(index_df,vix_df,on='Date',how='left')
    #print(index_df.head(5))

    
    expdt_df = expdt_df[expdt_df['ExpiryDate'] <= index_df['Date'].max()]

    print(expdt_df.head())

    #return
    
    batch_num = 1
    batches_df = pd.DataFrame(columns=['Date', 'Close', 'BatchNumber'])
    
    for i in range(len(expdt_df)):
        edt = expdt_df['ExpiryDate'].iloc[i]                
        #strikeprice = int(myround(stockprice,base=stock[2]))
        key = index_df[index_df['Date']==edt].index.values.astype(int)[0]
        #print(key)
        if key - days_window + 1 >= 0:
            index_window_df = index_df[key-days_window+1:key+1].copy()
            index_window_df['BatchNumber'] = batch_num
            index_window_df['ExpiryDay'] = edt
            index_window_df['StrikePrice'] = int(myround(index_window_df['Close'].iloc[0],sp_nearer))
            index_window_df.reset_index(inplace=True, drop=True)
        #print(index_window_df.head())
        #index_window_dict = index_window_df.to_dict()
        #batches_df.append(pd.DataFrame.from_dict(index_window_dict))
            batches_df = batches_df.append(index_window_df,ignore_index = True,sort=False)
        
        #print(batches_df.head())
        #index_window_dict['batchnumber'] = batch_num
        #print(index_window_dict)
        #break
        
        batch_num += 1
    
    #batches_df = batches_df[['Date','BatchNumber','Close','ExpiryDay']]
    #print(batches_df.head())
    batches_df['PutStrikePrice'] = batches_df['StrikePrice'] 
    batches_df['CallStrikePrice'] = batches_df['StrikePrice']
    
    #batches_df.to_csv(index + '_batch_by_' + str(days_window) +'.csv',header=True, sep=',', index=False)
    batches_df.reset_index(inplace=True,drop=True)
    #print(batches_df.head())
    #print(len(batches_df))
    
    #batches_df['PutPrice'] = batches_df.apply(price_from_dump,  axis=1, args=['PE'])
    
    batches_df['PutPrice'] = batches_df.apply(options_get_history,  axis=1, args=['PE'])
    batches_df['CallPrice'] = batches_df.apply(options_get_history,  axis=1, args=['CE'])
    
    
    
    batches_df['TotalPrice'] = batches_df['PutPrice'] + batches_df['CallPrice']
    
    #print(batches_df.head())
    
    
    batches_df['Investment'] = round((batches_df['PutPrice'] + batches_df['CallPrice']) * index_lot, 2)
    
    
#    cal_premium = []
#    cal_ix_change = []
#    cal_ix_pchange = []
#    for i in range(len(batches_df)):
#        if (i+1) % days_window == 1:
#            first_pre = batches_df['Premium'].iloc[i]
#            first_ic = batches_df['Close'].iloc[i]
#        cal_premium.append(first_pre - batches_df['Premium'].iloc[i])
#        cal_ix_change.append(batches_df['Close'].iloc[i] - first_ic)
#        cal_ix_pchange.append((batches_df['Close'].iloc[i] - first_ic) * 100 / batches_df['Close'].iloc[i])
#            
#    #print(cal_pre)
#    batches_df['Profit'] = cal_premium
#    batches_df['IndexChange'] = cal_ix_change
#    batches_df['Index%Change'] = cal_ix_pchange
#    
    
    batches_df['Flag'] = ''
    
    #batches_df['Flag'] = batches_df.apply(lambda x: 'E' if (x['Date'] == x['ExpiryDay']) else '', axis=1)
    
    batches_df.loc[batches_df.groupby('BatchNumber')['Flag'].head(1).index, 'Flag'] = 'S'
    batches_df.loc[batches_df.groupby('BatchNumber')['Flag'].tail(1).index, 'Flag'] = 'E'
    
    batches_df = batches_df[(batches_df['PutPrice'] != 0) & (batches_df['CallPrice'] != 0)]
    
    #batches_df['ExpiryFlag'] = batches_df.apply(lambda x: 'Y' if (x['Date'] == x['ExpiryDay']) else '', axis=1)
    
    batches_df['TotalPrice'] = batches_df['TotalPrice'].apply(lambda x: round(x,2))
    batches_df['Investment'] = batches_df['Investment'].apply(lambda x: round(x,2))
    #batches_df['Profit'] = batches_df['Profit'].apply(lambda x: round(x,2))
    #batches_df['IndexChange']  = batches_df['IndexChange'].apply(lambda x: round(x,2))
    #batches_df['Index%Change']  = batches_df['Index%Change'].apply(lambda x: round(x,2))
    
    
    batches_df.to_csv('{0}_output_lead-{1}.csv'.format(index,return_dayname(days_window)),header=True, sep=',', index=False)
    options_df.to_csv(option_file, header=True, sep=',', index=False)
    
    #sum_df = batches_df[batches_df['Flag'] == 'E']
    #sum_df = sum_df[['Date','Profit']]
    #sum_df['WindowSpread'] = '{0}'.format(return_dayname(days_window))
    #return sum_df
    

if __name__ == '__main__':
    buy_vertical(5)
    #days_window, sp_spread = 2, 100
    #sp_c = [(2,100), (3,200), (4,300), (5,400), (6,500)]
#    sp_c = [(3,200), (4,300), (5,400), (6,500)] # (2,100) is not profitable
#    
#    summary_df = pd.DataFrame(columns=['WindowSpread','Date', 'Profit'])
#    
#    for i, j in sp_c:
#        temp_df = None
#        print('\nWorking on window {0} & spread {1}\n'.format(str(i), str(j)))
#        temp_df = spread_combo(i,j)
#        summary_df = summary_df.append(temp_df,ignore_index = True,sort=False)
#    
#    summary_df.reset_index(inplace=True, drop=True)
#    summary_df.to_csv('Summary_output_{0}.csv'.format(os.path.basename(__file__)),header=True, sep=',', index=False)
    