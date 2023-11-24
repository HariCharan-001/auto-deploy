import os
import time
import sys

saarang_dir = '/var/www/Saarang2024'
sleep_time = int(sys.argv[1])
debug = False

if(len(sys.argv) > 2):
    debug = sys.argv[2]

def frontend_deploy(repo, commit_id):
    os.chdir(saarang_dir + '/' + repo)
    latest_commit_id = os.popen('git rev-parse HEAD').read().strip()

    if(debug == 'true'):
        print("Repo", repo, '\n', "Commit ID", commit_id, '\n', "Latest Commit ID", latest_commit_id, '\n')

    if latest_commit_id == commit_id:
        return latest_commit_id

    os.system('git pull')
    os.system('npm install')
    os.system('npm run build')

    os.system('sudo systemctl restart nginx')

    return latest_commit_id

def backend_deploy(repo, commit_id):
    os.chdir(saarang_dir + '/' + repo)
    latest_commit_id = os.popen('git rev-parse HEAD').read().strip()

    if(debug == 'true'):
        print("Repo", repo, '\n', "Commit ID", commit_id, '\n', "Latest Commit ID", latest_commit_id, '\n')

    if latest_commit_id == commit_id:
        return latest_commit_id

    os.system('git pull')
    os.system('yarn install')
    os.system('yarn build')
    os.system('pm2 stop ' + repo)
    os.system('pm2 start dist/index.js --name ' + repo + ' -- prod Dev24Ops$') 

    return latest_commit_id

while(True):
    try:
        repo_list = open('repo_list.txt', 'r')
        new_content = ''

        for line in repo_list:
            repo, type, commit_id = line.split()

            if type == 'frontend':
                commit_id = frontend_deploy(repo, commit_id)

            elif type == 'backend':
                commit_id = backend_deploy(repo, commit_id)

            new_content += repo + ' ' + type + ' ' + commit_id + '\n'

        repo_list.close()

        with open('repo_list.txt', 'w') as repo_list:
            repo_list.write(new_content)
            print(new_content)
            
        repo_list.close()

        time.sleep(sleep_time)
    
    except Exception as e:
        print(e)
        time.sleep(sleep_time)
