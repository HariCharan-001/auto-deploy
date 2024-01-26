import os
import time
import sys
import psycopg2
import threading 
import random
import logging
from logging.handlers import RotatingFileHandler

# config variables, remain constant throughout the execution
base_dir = '/var/www'
db_pwd = 'postgres'
sleep_time = int(30)
log_dir = base_dir + '/Saarang2024/auto-deploy/logs'
univ_log_file = log_dir + '/auto_deploy.log'
max_log_file_size = 5   # in MB

cur_repo = ''
repo_status = {}

if(len(sys.argv) > 1):
    db_pwd = sys.argv[1]

if(len(sys.argv) > 2):
    sleep_time = int(sys.argv[2])

def establish_connection():
    try:
        connection = psycopg2.connect(
            user = "postgres",
            password = db_pwd,
            host = "127.0.0.1",
            port = "5432",
            database = "auto_deploy"
        )

        logger.info(str(connection.get_dsn_parameters()) + "\n")

    except (Exception, psycopg2.Error) as error :
        logger.info("Error while connecting to PostgreSQL : " + str(error)) 
        exit()

    return connection

# create a log file handler that rotates log files when they reach max_log_file_size
handler = RotatingFileHandler(univ_log_file, maxBytes= max_log_file_size * 1000 * 1000, backupCount=5)     

# create a formatter that includes the timestamp, log level, and message
formatter = logging.Formatter('%(asctime)s %(message)s\n', datefmt='%Y-%m-%d %H:%M:%S')

# set the formatter for the handler
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def run_command(command):
    global cur_repo, log_dir

    log_path = log_dir + '/' + cur_repo + '.log'
    os.system(command + ' >> ' + log_path + ' 2>&1')

    log_file_size = os.path.getsize(log_path) / 1000 / 1000
    if(log_file_size > max_log_file_size):
        os.system('rm ' + log_path)
        logger.info('Removed log file ' + log_path + ' as it exceeded max size of ' + str(max_log_file_size) + ' MB' + '\n')
        os.system('touch ' + log_path)

def get_latest_commit_id(repo_path):
    os.chdir(repo_path)
    run_command('git pull')
    latest_commit_id = os.popen('git rev-parse HEAD').read().strip()

    return latest_commit_id

def update_repo(repo, latest_commit_id, repo_status):
    global cursor, connection
    cursor.execute("UPDATE repos SET latest_commit_id = '%s', status = '%s', last_updated = '%s' WHERE repo = '%s'" % (latest_commit_id, repo_status, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), repo))
    connection.commit()

def frontend_deploy(repo, latest_commit_id):
    global cur_repo, repo_status
    cur_repo = repo.split('/')[-1]

    try:
        logger.info('Deploying ' + repo + '\n')
        run_command('npm install')
        run_command('npm run build')
        logger.info('build successful for ' + repo + '\n')

        repo_status[cur_repo] = 'running'

    except:
        logger.info('build failed for ' + repo + '\n')
        repo_status[cur_repo] = 'failed'

    update_repo(repo, latest_commit_id, repo_status[cur_repo])

def backend_deploy(repo, latest_commit_id):
    global cur_repo, repo_status
    cur_repo = repo.split('/')[-1]

    try:
        logger.info('Deploying ' + repo + '\n')
        run_command('yarn install')
        run_command('yarn build')
        logger.info('build successful for ' + repo + '\n')

        run_command('pm2 restart dist/index.js --name ' + cur_repo + ' -- prod ' + db_pwd)
        logger.info('Restarted ' + repo + '\n')

        repo_status[cur_repo] = 'running'
    
    except:
        logger.info('failed to deploy ' + repo + '\n')
        repo_status[cur_repo] = 'failed'

    update_repo(repo, latest_commit_id, repo_status[cur_repo])




connection = establish_connection()
cursor = connection.cursor()
logger.info('Connected to PostgreSQL' + '\n' )

while(True):
    try:
        logger.info("Checking for updates: " + '\n')

        try:
            cursor.execute("SELECT * FROM repos")
            repos = cursor.fetchall()

        except(Exception, psycopg2.Error) as error:
            logger.info("Error while fetching data from repos table: " + str(error))
            continue

        for repo in repos:
            # skip if repo is disabled
            if(repo[6] == 'false'):
                logger.info('Skipping ' + repo[1] + ' as it is disabled' + '\n')
                continue

            repo_path = base_dir + '/' + repo[1]
            repo_type = repo[2]
            latest_commit_id = repo[3]

            if(get_latest_commit_id(repo_path) == latest_commit_id):
                logger.info('Latest commit id: ' + latest_commit_id + ', No updates found for ' + repo[1] + '\n')
                continue

            else:
                latest_commit_id = get_latest_commit_id(repo_path)
                logger.info('Latest commit id: ' + latest_commit_id + ', Updates found for ' + repo[1] + '\n')

            thread = None
            if(repo_type == 'frontend'):
                thread = threading.Thread(target=frontend_deploy, args=(repo[1], latest_commit_id,))
            else:
                thread = threading.Thread(target=backend_deploy, args=(repo[1], latest_commit_id,))

            thread.start()
            thread.join()
    
    except (Exception, psycopg2.Error) as error :
        logger.info("Error : " + str(error))

    time.sleep(sleep_time)