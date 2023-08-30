import time

# convert string to struct_time
struct_time = time.strptime("2022-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")

# convert struct_time to timestamp
timestamp = time.mktime(struct_time)

print(timestamp)