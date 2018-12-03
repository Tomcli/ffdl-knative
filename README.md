# knative-containers

In this directory, run the following to build each container

1. fairness check
```shell
docker build -t <docker_namespace>/fairness-check . -f Dockerfile-fairness
```
2. robustness check 
```shell
docker build -t <docker_namespace>/robustness-check . -f Dockerfile-robustness
```
3. model deployment
```shell
docker build -t <docker_namespace>/model-deployment . -f Dockerfile-deployment
```
