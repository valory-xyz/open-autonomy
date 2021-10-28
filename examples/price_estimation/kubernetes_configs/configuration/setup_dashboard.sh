#! /bin/bash
pkill -9 -f "kubectl proxy"
kubectl proxy &
echo "token for login: $(kubectl describe secret $(kubectl get secret | grep admin | awk '{print $1}') | grep token: | awk '{print $2}')"
echo $(kubectl describe secret $(kubectl get secret | grep admin | awk '{print $1}') | grep token: | awk '{print $2}') | xclip -sel c



URL="http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/login"

echo """
to view the dashboard navigate to
$URL"""
firefox $URL &
