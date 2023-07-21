# SummSlim

动态分析与启发式方法结合的镜像精简工具。

## 用法

先clone本repo。

然后进入本repo的目录，创建两个辅助文件夹：

```shell
mkdir merged
mkdir docker_run_example
```

在docker_run_example中可以存放启动容器的示例命令，例如：

```shell
touch nginx
nano nginx
# 然后写入以下命令文本
# docker run --rm -P nginx
```

接下来就可以进行精简了：

```shell
sudo python3 summslim.py image_name
```

## ToDo

- 完善一下 umount ./merged 代码
- 完善一下初次运行时清空 ./image_files/0_build_dir 文件夹报错的问题
- 删除多余的注释
- 将启动部分修改为静态分析
- 测试代码中的zzcslim也改掉了，还没测试有没有问题，不过这些代码大概率也不会再用了