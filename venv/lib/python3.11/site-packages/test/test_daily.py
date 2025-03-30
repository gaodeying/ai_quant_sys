"""
@author: dayan
@group : Tushare(https://waditu.com)
"""
import tushare as ts

def test_daily():
    pro = ts.pro_api()
    df = pro.anns(start_date='2009-06-27')
    print(df)


if __name__ == '__main__':
    test_daily()
