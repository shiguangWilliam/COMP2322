import time
ts_tuple = time.strptime("2023-10-01 12:00:00", "%Y-%m-%d %H:%M:%S")
ts = time.mktime(ts_tuple)
print(ts_tuple) # 1696147200.0