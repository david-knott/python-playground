# python-playground



```
winpty docker run -it --rm --name my-running-script -v D:\\Workspace\\Personal\\python-playground://usr/src/app -w //usr/src/app python:3 python basic_test.py
```




## Trouble

Docker volume mount is not working

```
docker run  -v D:\\Workspace\Personal\python-playground/://usr/src/app/ 2e40e235e3f3 ls //usr/src/app/
```