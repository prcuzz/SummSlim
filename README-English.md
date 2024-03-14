# SummSlim

This is a container image debloating tool.

## usage

clone this repo.

Then go to the directory of this repo and create two secondary folders:

```shell
mkdir merged
mkdir docker_run_example
```

In docker_run_example dir, you can store sample command to start containers, such as:

```shell
touch nginx
nano nginx
# Then write the following command text
# docker run --rm -P nginx
```

Next run our tool to debloat：

```shell
sudo python3 summslim.py [image_name]
```

