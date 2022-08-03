import git
import re
import urllib3
import web3

def define_env(env):
    "Hook function"

    @env.macro
    def get_hash(name):
        try:
            g = git.cmd.Git()
            blob = g.ls_remote('https://github.com/valory-xyz/open-autonomy', sort='-v:refname', tags=True)
            last_tag = blob.split('\n')[0].split('/')[-1]
            hashes_url = 'https://raw.githubusercontent.com/valory-xyz/open-autonomy/' + last_tag + '/packages/hashes.csv'
            http = urllib3.PoolManager()
            response = http.request('GET', hashes_url)
            data = response.data.decode('utf-8')
            results = [x.strip() for x in re.findall(r"^.*" + name + ",(.+?)$", data, re.DOTALL | re.MULTILINE)]
            if len(results) == 1:
                return results[0]
            else:
                return "[HASH_VALUE]"
        except:
            return "[HASH_VALUE]"
        