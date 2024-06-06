import psutil
from influxdb import InfluxDBClient
import logging
from logging.handlers import RotatingFileHandler
import time
import sys

# config variables, remain constant throughout the execution
log_dir = '/home/ubuntu/auto-deploy/logs'
univ_log_file = log_dir + '/monitor_memory.log'
max_log_file_size = 5   # in MB

database = 'memory_usage'
db_username = 'hari'
db_pwd = 'Lambo300k$'

frequency = 5  # in minutes

if(len(sys.argv) > 1):
    db_pwd = sys.argv[1]

# create a log file handler that rotates log files when they reach max_log_file_size
handler = RotatingFileHandler(univ_log_file, maxBytes= max_log_file_size * 1000 * 1000, backupCount=5)

# create a formatter that includes the timestamp, log level, and message
formatter = logging.Formatter('%(asctime)s %(message)s\n', datefmt='%Y-%m-%d %H:%M:%S')

# set the formatter for the handler
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

logger.info("Log file " + univ_log_file + " initialized")



try:
    # Create an InfluxDB client
    client = InfluxDBClient(host='localhost', port=8086, username=db_username, password=db_pwd)

    # Connect to a database (will create it if not found)
    client.switch_database(database)

    logger.info("InfluxDB client initialized")

    result = client.query('show measurements')
    logger.info("Measurements in database: " + str(result))

except Exception as e:
    logger.error("Error while initializing InfluxDB client: " + str(e))
    exit()



def push_memory_usage_influxDB(used, free, total):
    json_body = [
        {
            "measurement": "memory_usage",
            "tags": {},
            "fields": {
                "used": used,
                "free": free,
                "total": total
            }
        }
    ]

    client.write_points(json_body)
    logger.info("Memory usage pushed to InfluxDB: " + str(used) + " GB")


logger.info("Monitoring memory usage every " + str(frequency) + " minutes")
while(True):
    memory_usage = psutil.virtual_memory()
    used = memory_usage.used / (1024 ** 3)
    free = memory_usage.available / (1024 ** 3)
    total = memory_usage.total / (1024 ** 3)

    push_memory_usage_influxDB(used, free, total)

    time.sleep(frequency * 60)