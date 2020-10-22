
PYCSW_DOCKER_IMAGE=latest

convert:
	PYCSW_DOCKER_IMAGE=$(PYCSW_DOCKER_IMAGE) kompose convert --volumes hostPath

up:
	kubectl apply -f db-data-persistentvolumeclaim.yaml
	kubectl apply -f db-deployment.yaml
	kubectl apply -f db-service.yaml
	kubectl apply -f pycsw-configmap.yaml
	kubectl apply -f pycsw-deployment.yaml
	kubectl apply -f pycsw-service.yaml

down:
	kubectl delete service pycsw
	kubectl delete service db
	kubectl delete deployment pycsw
	kubectl delete deployment db

remove-volumes:
	kubectl delete configmap pycsw-config
	kubectl delete PersistentVolumeClaim db-data

open:
	minikube service pycsw --url

restart: down up

status:
	kubectl get all -o wide
