import datetime
import os

result_file = r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine\test_python.txt"

with open(result_file, "w") as f:
    f.write(f"Python is working at {datetime.datetime.now()}\n")
    f.write(f"Current directory: {os.getcwd()}\n")
    f.write(f"Python version: {os.sys.version}\n")

print(f"✓ Test complete - check {result_file}")
