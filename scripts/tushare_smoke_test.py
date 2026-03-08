import os, json
import tushare as ts


def main():
    token = os.getenv("TUSHARE_TOKEN")
    print("token_present", bool(token))
    if not token:
        raise SystemExit("TUSHARE_TOKEN missing")

    pro = ts.pro_api(token)
    out = {}

    df1 = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    out['stock_basic_rows'] = len(df1)
    out['stock_basic_sample'] = df1.head(3).to_dict('records')

    df2 = pro.daily(ts_code='000001.SZ', start_date='20260101', end_date='20260307')
    out['daily_rows'] = len(df2)
    out['daily_sample'] = df2.head(3).to_dict('records')

    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
