
from __future__ import absolute_import
from __future__ import print_function

from nsepy import get_history
from datetime import date, timedelta, datetime
from dateutil import rrule
import dateutil.parser
import os
import calendar, pandas as pd
from dateutil.relativedelta import relativedelta, TH
import matplotlib.pyplot as plt

#stock = ['NIFTY 50', 'NIFTY', 100, 3, 75]
stock = ['NIFTY 50', 'NIFTY', 50, 2, 75]
#stock = ['NIFTY BANK', 'BANKNIFTY', 300, 3, 20]
#stock = ['NIFTY BANK', 'BANKNIFTY', 100, 2, 20]

def SIP(start_date, period_of_months): 
    calendar.setfirstweekday(calendar.MONDAY)
    
    #start_date = date(2018,9,3)
    sell_days_before_expiry = 0
    #period_of_months = 1
     

    
    mfd = date(start_date.year, start_date.month, 1)
    
    week_day = calendar.monthrange(mfd.year, mfd.month)[0]
    
    add_days = 0
    if week_day == 5:
        add_days = 2
    if week_day == 6:
        add_days = 1
    
    mfwd = mfd + timedelta(days=add_days)
    nextnmfd = mfwd + relativedelta(months=period_of_months-1)
    nextnmeom = nextnmfd + relativedelta(day=calendar.monthrange(nextnmfd.year, nextnmfd.month)[1])
    expiry_date = nextnmeom + relativedelta(weekday=TH(-1))
    
    
    #print(mfwd)
    nifty_fd = get_history(symbol=stock[0],start=mfwd,end=mfwd + timedelta(days=3),index=True)
    #print(nifty_fd['Close'])
    nifty_price = nifty_fd['Close'].values[0]
    strike_price = int(round(nifty_price, -2))
    #print(strike_price)
    
    nifty_opt_puts = get_history(symbol=stock[1],
                            start=mfwd,
                            end=expiry_date,
                            index=True,
                            option_type='PE',
                            strike_price=strike_price,
                            expiry_date=expiry_date)
    
    #nifty_opt_puts[['Close']].plot()
    #print(nifty_opt_puts[['Close']].head())
    #print(nifty_opt_puts[['Close']].tail())
    #print(mfwd,expiry_date,strike_price)
    nifty_opt_calls = get_history(symbol=stock[1],
                            start=mfwd,
                            end=expiry_date,
                            index=True,
                            option_type='CE',
                            strike_price=strike_price,
                            expiry_date=expiry_date)
    
    #nifty_opt_calls[['Close']].plot()
    #print(nifty_opt_calls.columns)
    #print(nifty_opt_calls.head())
    
    lot_size = 75
    
    calls_puts_date = nifty_opt_calls.index.values
    #print(calls_puts_date)
    first_price_date, last_price_date = calls_puts_date[0], calls_puts_date[-sell_days_before_expiry-1]
    nifty_ld = get_history(symbol=stock[0],start=last_price_date,end=last_price_date,index=True)
    nifty_ld_price = nifty_ld['Close'][0]
    
    calls_puts = list(zip(nifty_opt_calls['Close'], nifty_opt_puts['Close']))
    
    first_price, last_price = calls_puts[0], calls_puts[-sell_days_before_expiry-1]
    
    
    call_diff = last_price[0] - first_price[0]
    put_diff = last_price[1] - first_price[1]
    
    investment_value = (first_price[0] + first_price[1]) * lot_size
    current_value = (last_price[0] + last_price[1]) * lot_size
    
    profit = lot_size * (call_diff + put_diff)
    profit_percent = (profit * 100 / investment_value)
    
    print('******************** {0}     ********************'.format(start_date.date().strftime("%B %Y")))
    print('On {0}, {4} was {1:.2f}, strike price chosen as {2:.2f} with expiry on {3}'.format(mfwd,nifty_price,strike_price,expiry_date, stock[0]))
    print('On {3}, Call buy price : {0:.2f}  Call sell price : {1:.2f} Difference : {2:.2f} Profit : {4:.2f}'.format(first_price[0],last_price[0], call_diff, first_price_date, call_diff * lot_size))
    print('On {3}, Put buy price  : {0:.2f}  Put sell price  : {1:.2f} Difference : {2:.2f} Profit : {4:.2f}'.format(first_price[1],last_price[1], put_diff, last_price_date, put_diff * lot_size))
    print('On {0}, {2} was {1:.2f}'.format(last_price_date, nifty_ld_price, stock[0]))
    print()
    print('Investment    : {0:.2f}'.format(investment_value))
    print('Current Value : {0:.2f}'.format(current_value))
    print('Profit        : {0:.2f} ({1:.2f} %)'.format(profit, profit_percent))
    print()
    #print('**************************************************')
    return nifty_ld_price, profit_percent


def run_SIP(start, period_of_months):
    #start = date(2018,8,1)
    month_period = 8
    monthslater = start + relativedelta(months=(month_period-1))
    
    temp_dict = {}
    
    for start_date in rrule.rrule(rrule.MONTHLY, dtstart=start, until=monthslater):
        nifty_ld_price, profit_percent = SIP(start_date, period_of_months)
        temp_dict[start_date] = {'ProfitPercent': profit_percent,
                                'NiftyPrice': nifty_ld_price,
                                }
    df = pd.DataFrame.from_dict(temp_dict, orient='index')
    df[['NiftyPrice','ProfitPercent']].plot(secondary_y = 'ProfitPercent')
    #ax = plt.gca()
    #df.plot(kind='scatter', x=df.index, y='NiftyPrice',color='red', ax=ax)
    #df.plot(kind='scatter', x=df.index, y='ProfitPercent',color='blue', ax=ax)
    #plt.show()

def run_single(start, period_of_months):
    calendar.setfirstweekday(calendar.MONDAY)
    
    #start_date = start
    sell_days_before_expiry = 0
    
    
    mfwd = start
    nextnmfd = mfwd + relativedelta(months=period_of_months-1)
    nextnmeom = nextnmfd + relativedelta(day=calendar.monthrange(nextnmfd.year, nextnmfd.month)[1])
    expiry_date = nextnmeom + relativedelta(weekday=TH(-1))
    
    if expiry_date <= mfwd:
        period_of_months = period_of_months + 1
        nextnmfd = mfwd + relativedelta(months=period_of_months-1)
        nextnmeom = nextnmfd + relativedelta(day=calendar.monthrange(nextnmfd.year, nextnmfd.month)[1])
        expiry_date = nextnmeom + relativedelta(weekday=TH(-1))
        
    #print(expiry_date)
    
    nifty_fd = get_history(symbol=stock[0],start=mfwd, end=mfwd + timedelta(days=3), index=True)
    #print(nifty_fd['Close'])
    nifty_price = nifty_fd['Close'].values[0]
    strike_price = int(round(nifty_price, -2))
    #print(strike_price)
    
    nifty_opt_puts = get_history(symbol=stock[1],
                            start=mfwd,
                            end=expiry_date,
                            index=True,
                            option_type='PE',
                            strike_price=strike_price,
                            expiry_date=expiry_date)
    
    #nifty_opt_puts[['Close']].plot()
    #print(nifty_opt_puts[['Close']].head())
    #print(nifty_opt_puts[['Close']].tail())
    #print(mfwd,expiry_date,strike_price)
    nifty_opt_puts.columns = [i + "_p" for i in nifty_opt_puts.columns]
    nifty_opt_calls = get_history(symbol=stock[1],
                            start=mfwd,
                            end=expiry_date,
                            index=True,
                            option_type='CE',
                            strike_price=strike_price,
                            expiry_date=expiry_date)
    nifty_opt_calls.columns = [i + "_c" for i in nifty_opt_calls.columns]
    #nifty_opt_calls[['Close']].plot()
    #print(nifty_opt_calls.columns)
    #print(nifty_opt_calls.head())
    
    calls_puts = pd.concat([nifty_opt_calls,nifty_opt_puts],axis=1)
    
    lot_size = 75
    
    
    
    #print(calls_puts.columns)
    #print(calls_puts.head())
    calls_puts['InitialValue'] = (calls_puts['Close_p'][0] + calls_puts['Close_c'][0]) * lot_size
    calls_puts['CurrentValue'] = (calls_puts['Close_p'] + calls_puts['Close_c']) * lot_size
    calls_puts['Profit'] = calls_puts['CurrentValue'] - calls_puts['InitialValue'] 
    ax1=plt.subplot(2, 2, 1)
    ax2=plt.subplot(2, 2, 2)
    ax3=plt.subplot(2, 2, 3)
    
    calls_puts[['Close_p','Close_c']].plot(ax=ax1)
    calls_puts[['InitialValue','CurrentValue']].plot(ax=ax2)
    calls_puts[['Profit']].plot(ax=ax3)
    
    for tick1, tick2, tick3 in zip(ax1.get_xticklabels(),ax2.get_xticklabels(), ax3.get_xticklabels()):
        tick1.set_rotation(45)
        tick2.set_rotation(45)
        tick3.set_rotation(45)
        
    
    plt.show()
    return
    
    
def single_before_expiry(start_date, period_of_months):
    
    calendar.setfirstweekday(calendar.MONDAY)
    
    #start_date = date(2018,9,3)
    sell_days_before_expiry = 0
    #period_of_months = 1
     
    
    mfd = date(start_date.year, start_date.month, 1)
    
    week_day = calendar.monthrange(mfd.year, mfd.month)[0]
    
    add_days = 0
    if week_day == 5:
        add_days = 2
    if week_day == 6:
        add_days = 1
    
    mfwd = mfd + timedelta(days=add_days)
    nextnmfd = mfwd + relativedelta(months=period_of_months-1)
    nextnmeom = nextnmfd + relativedelta(day=calendar.monthrange(nextnmfd.year, nextnmfd.month)[1])
    expiry_date = nextnmeom + relativedelta(weekday=TH(-1))
    
    from pandas.tseries.offsets import BDay
    mfwd = expiry_date - BDay(3)
    #mfwd = datetime.strptime(str(mfwd).split()[0],'%Y-%m-%d')
    mfwd = dateutil.parser.parse(str(mfwd)).date()
    
    #print(mfwd)
    nifty_fd = get_history(symbol=stock[0],start=mfwd, end=mfwd + timedelta(days=3),index=True)
    #print(nifty_fd['Close'])
    nifty_price = nifty_fd['Close'].values[0]
    strike_price = int(round(nifty_price, -2))
    #print(strike_price)
    
    nifty_opt_puts = get_history(symbol=stock[1],
                            start=mfwd,
                            end=expiry_date,
                            index=True,
                            option_type='PE',
                            strike_price=strike_price,
                            expiry_date=expiry_date)
    
    #nifty_opt_puts[['Close']].plot()
    #print(nifty_opt_puts[['Close']].head())
    #print(nifty_opt_puts[['Close']].tail())
    #print(mfwd,expiry_date,strike_price)
    nifty_opt_calls = get_history(symbol=stock[1],
                            start=mfwd,
                            end=expiry_date,
                            index=True,
                            option_type='CE',
                            strike_price=strike_price,
                            expiry_date=expiry_date)
    
    #nifty_opt_calls[['Close']].plot()
    #print(nifty_opt_calls.columns)
    #print(nifty_opt_calls.head())
    
    lot_size = 75
    
    calls_puts_date = nifty_opt_calls.index.values
    #print(calls_puts_date)
    first_price_date, last_price_date = calls_puts_date[0], calls_puts_date[-sell_days_before_expiry-1]
    
    nifty_ld = get_history(symbol=stock[0],start=last_price_date,end=last_price_date,index=True)
    nifty_ld_price = nifty_ld['Close'][0]
    
    calls_puts = list(zip(nifty_opt_calls['Close'], nifty_opt_puts['Close']))
    
    first_price, last_price = calls_puts[0], calls_puts[-sell_days_before_expiry-1]
    
    
    call_diff = last_price[0] - first_price[0]
    put_diff = last_price[1] - first_price[1]
    
    #investment_value = (first_price[0] + first_price[1]) * lot_size
    #current_value = (last_price[0] + last_price[1]) * lot_size
    
    #profit = lot_size * (call_diff + put_diff)
    #profit_percent = (profit * 100 / investment_value)
    
    print('******************** {0}     ********************'.format(start_date.date().strftime("%B %Y")))
    print('On {0}, {4} was {1:.2f}, strike price chosen as {2:.2f} with expiry on {3}'.format(mfwd,nifty_price,strike_price,expiry_date, stock[0]))
    print('On {3}, Call sell price : {0:.2f}  Call buy price : {1:.2f} Difference : {2:.2f} Profit : {4:.2f}'.format(first_price[0],last_price[0], -call_diff, first_price_date, -call_diff * lot_size))
    print('On {0}, {2} was {1:.2f}'.format(last_price_date, nifty_ld_price, stock[0]))
    print('On {3}, Put sell price  : {0:.2f}  Put buy price  : {1:.2f} Difference : {2:.2f} Profit : {4:.2f}'.format(first_price[1],last_price[1], -put_diff, last_price_date, -put_diff * lot_size))
    print()
    profit = (-call_diff) * lot_size + (-put_diff * lot_size)
    #print('Investment    : {0:.2f}'.format(investment_value))
    #print('Current Value : {0:.2f}'.format(current_value))
    #print('Profit        : {0:.2f} ({1:.2f} %)'.format(profit, profit_percent))
    #print()
    #print('**************************************************')
    return nifty_ld_price, profit #, profit_percent
    
    #return




def run_single_before_expiry(start, period_of_months):
    #start = date(2018,8,1)
    month_period = 11
    monthslater = start + relativedelta(months=(month_period-1))
    
    temp_dict = {}
    
    for start_date in rrule.rrule(rrule.MONTHLY, dtstart=start, until=monthslater):
        nifty_ld_price, profit = single_before_expiry(start_date, period_of_months)
        temp_dict[start_date] = {'Profit': profit,
                                'NiftyPrice': nifty_ld_price,
                                }
    df = pd.DataFrame.from_dict(temp_dict, orient='index')
    df['RunningProfit'] = df['Profit'].cumsum()
    df[['NiftyPrice','RunningProfit']].plot(secondary_y = 'RunningProfit')    
        


def myround(x, base):
    return base * round(x/base)


#def get_options_price_puts(start_date, expiry_date, strike_price):
def get_options_price_puts(row):  
    #print(row)
    start_date = datetime.strptime(row['Key'],'%Y-%m-%d') if isinstance(row['Key'],str) else row['Key']
    expiry_date =  datetime.strptime(row['ExpiryDate'],'%Y-%m-%d') if isinstance(row['ExpiryDate'],str) else row['ExpiryDate']
    strike_price = row['StrikePrice'] - stock[2]
    #if stock[0] == 'NIFTY BANK' and strike_price % 100 != 0:
    #    strike_price = strike_price - 50
        
    #print(start_date, expiry_date)
    #start_date = datetime.strptime(start_date,'%Y-%m-%d')
    #expiry_date = datetime.strptime(expiry_date,'%Y-%m-%d')
    #strike_price = x['StrikePrice']
    nifty_opt_puts = get_history(symbol=stock[1],
                        start=start_date,
                        end=start_date,
                        index=True,
                        option_type='PE',
                        strike_price=strike_price,
                        expiry_date=expiry_date)
    #print('hello1',nifty_opt_puts['Close'])
    
    try:
        return nifty_opt_puts['Close'][0], strike_price
    except:
        return None, strike_price


def get_options_price_calls(row):  
    #print(row)
    start_date = datetime.strptime(row['Key'],'%Y-%m-%d') if isinstance(row['Key'],str) else row['Key']
    expiry_date =  datetime.strptime(row['ExpiryDate'],'%Y-%m-%d') if isinstance(row['ExpiryDate'],str) else row['ExpiryDate']
    strike_price = row['StrikePrice'] + stock[2]
    #if stock[0] == 'NIFTY BANK' and strike_price % 100 != 0:
    #    strike_price = strike_price - 50

    #print(start_date, expiry_date)
    #start_date = datetime.strptime(start_date,'%Y-%m-%d')
    #expiry_date = datetime.strptime(expiry_date,'%Y-%m-%d')
    #strike_price = x['StrikePrice']
    nifty_opt_calls = get_history(symbol=stock[1],
                        start=start_date,
                        end=start_date,
                        index=True,
                        option_type='CE',
                        strike_price=strike_price,
                        expiry_date=expiry_date)
    #print('hello1',nifty_opt_calls['Close'])
    try:
        return (nifty_opt_calls['Close'][0], strike_price)
    except:
        return (None, strike_price)



def run_weekly(start):
    #start = date(2018,8,1)
    #month_period = 12
    #monthslater = start + relativedelta(months=(month_period-1))
    #print(datetime.now().date())
    
    lot_size = stock[4]
    print('Pulling {0} dump...'.format(stock[0]))
    if not os.path.exists(stock[0] + '_output_temp.csv'):
        nifty_all = pd.read_csv(stock[0] + '_data.csv')
        #nifty_all = nifty_all[nifty_all['Date']]
        #nifty_all = get_history(symbol="NIFTY 50", start=start, end=datetime.now().date(), index=True)
        nifty_all.index = nifty_all['Date'].apply(lambda x : datetime.strptime(x, '%d-%b-%y').date())
        nifty_all.drop(['Date','Turnover (Rs. Cr)','Shares Traded','Open','High','Low'], axis=1, inplace=True)
        #print(nifty_all.head())
        #return
        #temp_dict = {}
        #temp_dict['2019-03-01'] = {'Close': 10863.50}
        #temp_dict['2019-03-05'] = {'Close': 10987.45}
        #temp_dict['2019-03-06'] = {'Close': 11053.00}
        #temp_dict['2019-03-07'] = {'Close': 11058.20}
        #temp_dict['2019-03-08'] = {'Close': 11035.40}
        #temp_dict['2019-03-11'] = {'Close': 11065.50}
        #temp_dict['2019-03-12'] = {'Close': 11099.45}
        #temp_dict['2019-03-13'] = {'Close': 11113.00}
        #temp_dict['2019-03-14'] = {'Close': 11138.20}
        #temp_dict['2019-03-15'] = {'Close': 11045.40}
    
        
        #nifty_all = pd.DataFrame.from_dict(temp_dict, orient='index')
        #nifty_all['StrikePrice'] = nifty_all['Close'].apply(lambda x: int(myround(x)))
        nifty_all['Weekday'] = nifty_all.index
        nifty_all['Weekday'] = nifty_all['Weekday'].apply(lambda x: datetime.strptime(x,'%Y-%m-%d').weekday() if isinstance(x,str) else x.weekday())
        #nifty_all['Weekday'] = nifty_all['Weekday'].apply(lambda x: x.weekday())
        nifty_all['ExpiryDay'] = nifty_all['Weekday'].apply(lambda x: True if x == 3 else False)
        nifty_all['Group'] = 0
        
        counter = 1
        ids = []
        for i in range(len(nifty_all)):
            if not nifty_all['ExpiryDay'].iloc[i] :
                ids.append(i)
            else:
                for j in ids:
                    nifty_all['Group'].iloc[j] = counter
                nifty_all['Group'].iloc[i] = counter
                ids = []
                counter += 1
    
        nifty_all = nifty_all[nifty_all['Group'] != 0]
        
        #print('**** 1 *****')
        #print(nifty_all.head())
        #print(nifty_all.tail())
    
    
        nifty_all = nifty_all.groupby('Group').tail(stock[3])
        nifty_all['StrikePrice'] = nifty_all['Close'].apply(lambda x: int(myround(x,base=stock[2])))
        if stock[0] == 'NIFTY BANK':
            nifty_all['StrikePrice'] = nifty_all['StrikePrice'].apply(lambda x: x if (x + stock[2]) % 100  == 0 else (x - 50))
        
        #nifty_all = nifty_all[nifty_all['ExpiryDay'] == False]
        #nifty_all = nifty_all.groupby('Group').tail()
        nifty_all['Order'] = nifty_all.groupby('Group').cumcount()
        
        
        nifty_sp = nifty_all.groupby('Group').first()
        nifty_sp.drop(['Close','Weekday','ExpiryDay'], axis=1, inplace=True)
        #print(nifty_sp.head())
        nifty_all['StrikePrice'] = nifty_all['Group'].apply(lambda x: nifty_sp.loc[x,'StrikePrice'])
        nifty_all['Key'] = nifty_all.index
        nifty_ed = nifty_all.groupby('Group').last()
        nifty_ed.drop(['Close','StrikePrice','Weekday','ExpiryDay'], axis=1, inplace=True)
        #print(nifty_ed.head())
        #nifty_all.drop(['Key'], axis=1, inplace=True)
        
        
        
        nifty_all['ExpiryDate'] = nifty_all['Group'].apply(lambda x: nifty_ed.loc[x,'Key'])
        
        #print('**** 2 *****')
        #print(nifty_all.head())
        #print(nifty_all.tail())
        
        
        #nifty_all['PutPrice'] = get_options_price_puts(nifty_all.Key, nifty_all.ExpiryDate , nifty_all.StrikePrice)
        #print(nifty_all.groupby(['Key','ExpiryDate','StrikePrice']).head())
        #nifty_option_price = nifty_all.groupby(['Key','ExpiryDate','StrikePrice']).apply(get_options_price_puts, axis=1)
        #nifty_option_price = nifty_all.apply(get_options_price_puts, axis=1)
        nifty_all['PutPrice']  = nifty_all.apply(get_options_price_puts, axis=1)
        nifty_all['PutStrikePrice'] =  nifty_all['PutPrice'].apply(lambda x: x[1])
        nifty_all['PutPrice'] =  nifty_all['PutPrice'].apply(lambda x: x[0])
        
        
        nifty_all['CallPrice']  = nifty_all.apply(get_options_price_calls, axis=1)
        nifty_all['CallStrikePrice'] = nifty_all['CallPrice'].apply(lambda x: x[1])
        nifty_all['CallPrice'] =  nifty_all['CallPrice'].apply(lambda x: x[0])
        
        nifty_all['Premium']  = (nifty_all['PutPrice'] + nifty_all['CallPrice']) * lot_size
        #print(nifty_option_price,type(nifty_option_price))
        
        #nifty_all.to_csv(stock[0] + '_output_temp.csv',header=True, sep=',', index=False)
    else:
        nifty_all = pd.read_csv(stock[0] + '_output_temp.csv')
    print('Pull complete...')
    
    nifty_value_first = nifty_all.groupby('Group').first()
    nifty_all['Profit'] = nifty_all['Group'].apply(lambda x: nifty_value_first.loc[x,'Premium']) - nifty_all['Premium'] 
    nifty_all.loc[nifty_all['ExpiryDay'] == False, 'Profit'] = 0
    
    date1 = nifty_all['Key'].min()
    date2 = nifty_all['Key'].max()
    spread = stock[2]
    window = stock[3]
    
    print('**** 3 *****')
    print(nifty_all.head())
    print(nifty_all.tail())
    
    filename = '{0}_{1}_{2}_S{3}_W{4}.csv'.format(stock[0],date1,date2,spread*2,window)
    
    nifty_all.to_csv(filename, header=True, sep=',', index=False)
    
    from xlsxwriter.workbook import Workbook
    import csv
    
    
    
    workbook = Workbook(filename[:-4] + '.xlsx', {'strings_to_numbers': True})
    worksheet = workbook.add_worksheet()
    format1 = workbook.add_format({'num_format': '#,##0.00'})
                                   
    with open(filename, 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                worksheet.write(r, c, col)
    worksheet.set_column('I:I', 10, format1)
    worksheet.set_column('K:K', 10, format1)
    worksheet.set_column('M:N', 10, format1)
    workbook.close()
    
    
#    temp_dict = {}
#    
#    for start_date in rrule.rrule(rrule.MONTHLY, dtstart=start, until=monthslater):
#        nifty_ld_price, profit = single_before_expiry(start_date, period_of_months)
#        temp_dict[start_date] = {'Profit': profit,
#                                'NiftyPrice': nifty_ld_price,
#                                }
#    df = pd.DataFrame.from_dict(temp_dict, orient='index')
#    df['RunningProfit'] = df['Profit'].cumsum()
#    df[['NiftyPrice','RunningProfit']].plot(secondary_y = 'RunningProfit')    

def get_current_price_details():
    from nsetools import Nse
    nse = Nse()
    stockprice = nse.get_index_quote(stock[0])['lastPrice']
    #stockprice = q['lastPrice']
    strikeprice = int(myround(stockprice,base=stock[2]))
    callstrikeprice = strikeprice + stock[2]
    putstrikeprice = strikeprice - stock[2]
    
    print('For price {0}, sell calls @ strike {2} and puts @ {3}'.format(stockprice,strikeprice,callstrikeprice, putstrikeprice))    


if __name__ == '__main__':
    start = date(2019,1,1)
    print(stock)
    #period_of_months = 3
    #run_SIP(start, period_of_months)
    #run_single(start, period_of_months)
    #period_of_months = 1
    #run_single_before_expiry(start, period_of_months)
    run_weekly(start)
    
    #get_current_price_details()
    #stockprice = 29650.20
    #strikeprice = int(myround(stockprice,base=stock[2]))
    #callstrikeprice = strikeprice + stock[2]
    #putstrikeprice = strikeprice - stock[2]
    
    #print('For price {0}, sell calls @ strike {2} and puts @ {3}'.format(stockprice,strikeprice,callstrikeprice, putstrikeprice))
    
    
    
    
    



# =============================================================================
# 
# #Stock history
# sbin = get_history(symbol='SBIN',
#                     start=date(2015,1,1), 
#                     end=date(2015,1,10))
# sbin[[ 'VWAP', 'Turnover']].plot(secondary_y='Turnover')
# 
# """	Index price history
# 	symbol can take these values (These indexes have derivatives as well)
# 	"NIFTY" or "NIFTY 50",
# 	"BANKNIFTY" or "NIFTY BANK",
# 	"NIFTYINFRA" or "NIFTY INFRA",
#     	"NIFTYIT" or "NIFTY IT",
#     	"NIFTYMID50" or "NIFTY MIDCAP 50",
#     	"NIFTYPSE" or "NIFTY PSE"
# 	In addition to these there are many indices
# 	For full list refer- http://www.nseindia.com/products/content/equities/indices/historical_index_data.htm
# """
# nifty = get_history(symbol="NIFTY", 
#                     start=date(2015,1,1), 
#                     end=date(2015,1,10),
# 					index=True)
# nifty[['Close', 'Turnover']].plot(secondary_y='Turnover')
# 
# #Futures and Options historical data
# nifty_fut = get_history(symbol="NIFTY", 
# 			start=date(2015,1,1), 
# 			end=date(2015,1,10),
# 			index=True,
# 			futures=True, expiry_date=date(2015,1,29))
# 						
# stock_opt = get_history(symbol="SBIN",
# 			start=date(2015,1,1), 
# 			end=date(2015,1,10),
# 			option_type="CE",
# 			strike_price=300,
# 			expiry_date=date(2015,1,29))
# 
# #Index P/E ratio history
# nifty_pe = get_index_pe_history(symbol="NIFTY",
# 				start=date(2015,1,1), 
# 				end=date(2015,1,10))
# =============================================================================