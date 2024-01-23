import os
import time
import sys
import psycopg2
import threading 

# config variables, remain constant throughout the execution
base_dir = '/var/www'
db_pwd = 'postgres'
sleep_time = int(30)
log_dir = base_dir + '/Saarang2024/auto-deploy/logs'
univ_log_file = log_dir + '/auto_deploy.log'

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

        logToFile(str(connection.get_dsn_parameters()) + "\n")

    except (Exception, psycopg2.Error) as error :
        logToFile("Error while connecting to PostgreSQL : " + str(error)) 
        exit()

    return connection

def logToFile(message):
    global univ_log_file

    with open(univ_log_file, 'a') as log:
        log.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' ' + message + '\n')
        log.close()

def run_command(command):
    global cur_repo, log_dir

    log_path = log_dir + '/' + cur_repo + '.log'
    os.system(command + ' >> ' + log_path + ' 2>&1')

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
        logToFile('Deploying ' + repo + '\n')
        run_command('npm install')
        run_command('npm run build')
        logToFile('build successful for ' + repo + '\n')

        repo_status[cur_repo] = 'running'

    except:
        logToFile('build failed for ' + repo + '\n')
        repo_status[cur_repo] = 'failed'

    update_repo(repo, latest_commit_id, repo_status[cur_repo])

def backend_deploy(repo, latest_commit_id):
    global cur_repo, repo_status
    cur_repo = repo.split('/')[-1]

    try:
        logToFile('Deploying ' + repo + '\n')
        run_command('yarn install')
        run_command('yarn build')
        logToFile('build successful for ' + repo + '\n')

        run_command('pm2 restart dist/index.js --name ' + cur_repo + ' -- prod ' + db_pwd)
        logToFile('Restarted ' + repo + '\n')

        repo_status[cur_repo] = 'running'
    
    except:
        logToFile('failed to deploy ' + repo + '\n')
        repo_status[cur_repo] = 'failed'

    update_repo(repo, latest_commit_id, repo_status[cur_repo])




connection = establish_connection()
cursor = connection.cursor()
logToFile('Connected to PostgreSQL' + '\n' )

while(True):
    try:
        logToFile("Checking for updates: " + '\n')

        try:
            cursor.execute("SELECT * FROM repos")
            repos = cursor.fetchall()

        except(Exception, psycopg2.Error) as error:
            logToFile("Error while fetching data from repos table: " + str(error))
            continue

        for repo in repos:
            # skip if repo is disabled
            if(repo[6] == 'false'):
                logToFile('Skipping ' + repo[1] + ' as it is disabled' + '\n')
                continue

            repo_path = base_dir + '/' + repo[1]
            repo_type = repo[2]
            latest_commit_id = repo[3]

            if(get_latest_commit_id(repo_path) == latest_commit_id):
                logToFile('Latest commit id: ' + latest_commit_id + ', No updates found for ' + repo[1] + '\n')
                continue

            else:
                latest_commit_id = get_latest_commit_id(repo_path)
                logToFile('Latest commit id: ' + latest_commit_id + ', Updates found for ' + repo[1] + '\n')

            thread = None
            if(repo_type == 'frontend'):
                thread = threading.Thread(target=frontend_deploy, args=(repo[1], latest_commit_id,))
            else:
                thread = threading.Thread(target=backend_deploy, args=(repo[1], latest_commit_id,))

            thread.start()
            thread.join()
    
    except (Exception, psycopg2.Error) as error :
        logToFile("Error : " + str(error))

    time.sleep(sleep_time)