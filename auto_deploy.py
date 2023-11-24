import os
import time
import sys

saarang_dir = '/var/www/Saarang2024'
sleep_time = sys.argv[1]
debug = False

if(len(sys.argv) > 2):
    debug = sys.argv[2]

def frontend_deploy(repo, commit_id):
    os.chdir(saarang_dir + '/' + repo)
    latest_commit_id = os.popen('git rev-parse HEAD').read().strip()

    if(debug == 'true'):
        print("Repo", repo, '\n', "Commit ID", commit_id, '\n', "Latest Commit ID", latest_commit_id, '\n')

    if latest_commit_id == commit_id:
        return False

    os.system('git pull')
    os.system('npm install')
    os.system('npm run build')

    os.system('sudo systemctl restart nginx')

    return [True, latest_commit_id]

def backend_deploy(repo, commit_id):
    os.chdir(saarang_dir + '/' + repo)
    latest_commit_id = os.popen('git rev-parse HEAD').read().strip()

    if(debug == 'true'):
        print("Repo", repo, '\n', "Commit ID", commit_id, '\n', "Latest Commit ID", latest_commit_id, '\n')

    if latest_commit_id == commit_id:
        return False

    os.system('git pull')
    os.system('yarn install')
    os.system('yarn build')
    os.system('pm2 start dist/index.js --name ' + repo + ' -- prod Dev24Ops$') 

    return [True, latest_commit_id]

while(True):
    try:
        repo_list = open('repo_list.txt', 'r')
        new_content = ''

        for line in repo_list:
            repo, type, commit_id = line.split()
            result = None

            if type == 'frontend':
                result = frontend_deploy(repo, commit_id)

            elif type == 'backend':
                result = backend_deploy(repo, commit_id)

            if result:
                new_content += repo + ' ' + type + ' ' + result[1] + '\n'

        repo_list.close()

        repo_list = open('repo_list.txt', 'w')
        repo_list.write(new_content)
        repo_list.close()

        time.sleep(int(sleep_time))
    
    except Exception as e:
        print(e)
        time.sleep(sleep_time)
