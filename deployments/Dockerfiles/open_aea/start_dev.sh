sudo chown -R ubuntu:ubuntu /logs
sudo chown -R ubuntu:ubuntu /home/ubuntu/packages
sudo chown -R ubuntu:ubuntu /open-aea

pipenv install --skip-lock --dev

pipenv run python /home/ubuntu/watcher.py
