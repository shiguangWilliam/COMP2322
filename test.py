import os
import time

time_file = os.path.getmtime("text.txt")
print(time_file)
print(time.mktime(time.localtime(time_file)))