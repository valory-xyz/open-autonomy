#! /bin/bash
pkill -9 -f "kubectl proxy"
kubectl proxy &
echo $(kubectl describe secret $(kubectl get secret | grep admin | awk '{print $1}') | grep token: | awk '{print $2}') | xclip -sel c



firefox http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/login &
