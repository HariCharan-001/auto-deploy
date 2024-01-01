import os
import time
import sys

base_dir = '/var/www/'
db_pwd = 'postgres'
sleep_time = int(30)

if(len(sys.argv) > 1):
    db_pwd = sys.argv[1]

if(len(sys.argv) > 2):
    sleep_time = int(sys.argv[2])

def get_latest_commit_id(repo):
    os.chdir(base_dir + '/' + repo)
    os.system('git fetch origin')
    latest_commit_id = os.popen('git rev-parse origin/main').read().strip()
    return latest_commit_id

def frontend_deploy(repo, commit_id):
    latest_commit_id = get_latest_commit_id(repo)
    print("Repo", repo, '\n', "Commit ID", commit_id, '\n', "Latest Commit ID", latest_commit_id, '\n')

    if latest_commit_id == commit_id:
        return latest_commit_id

    os.system('git pull')
    os.system('npm install')
    os.system('npm run build')
    print('build successful')

    return latest_commit_id

def backend_deploy(repo, commit_id):
    latest_commit_id = get_latest_commit_id(repo)
    print("Repo", repo, '\n', "Commit ID", commit_id, '\n', "Latest Commit ID", latest_commit_id, '\n')

    if latest_commit_id == commit_id:
        return latest_commit_id

    os.system('git pull')
    os.system('yarn install')
    os.system('yarn build')
    print('build successful')

    os.system('pm2 stop ' + repo)
    os.system('pm2 start dist/index.js --name ' + repo + ' -- prod ' + db_pwd)
    print('Restarted ' + repo)

    return latest_commit_id

while(True):
    try:
        print("Checking for updates: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), '\n')

        repo_list = open('repo_list.txt', 'r')
        new_content = ''
        old_content = ''

        for line in repo_list:
            repo, type, commit_id = line.split()
            old_content += line

            if type == 'frontend':
                commit_id = frontend_deploy(repo, commit_id)

            elif type == 'backend':
                commit_id = backend_deploy(repo, commit_id)

            new_content += repo + ' ' + type + ' ' + commit_id + '\n'

        repo_list.close()

        if(not (new_content == old_content) ):
            with open('repo_list.txt', 'wb', 0) as repo_list:
                repo_list.write(new_content.encode())
                repo_list.flush()
                os.fsync(repo_list.fileno())
                print("Updated repo_list.txt")
            
            repo_list.close()

        time.sleep(sleep_time)
    
    except Exception as e:
        print(e)
        time.sleep(sleep_time)
