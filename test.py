import os
import time
print(os.path.getmtime("text.txt"))
print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime("text.txt"))))