FileSystem.exe          启动系统

basic.py                包括底层数据结构的定义以及底层函数的架构
core.py                 包括直接调用的用户操作函数
main.py                 启动系统
FileSysSim.pickle       文件系统本地存储

其中 文件系统本地存储 的文件名在 FileSystem.py 中更改，更改后需要重新存储并打包（没有python环境无法打包）

具体打包方法为：
安装 pyinstaller 后，在 FileSystem.py 所在路径打开终端
输入命令 pyinstaller -F -c FileSystem.py 即可

若没有系统本地存储(FileSysSim.pickle)，将使用初始化后的系统

本系统中可以且仅可以使用以下命令：
# h
    查看帮助
# touch + path
    新建一个空的文件并命名
# rm + path
    删除某个文件或目录
# ls + path
    查看当前目录下文件和目录
# mkdir + path
    新建目录
# rmdir + path
    移除目录
# cd + path
    进入目录
# cat + path
    输出 文件内容
# cat + str + '>' + path
    覆盖 文件内容
# cat + str + '>>' + path
    追加 文件内容
# disk
    查看磁盘剩余空间
# exit
    退出系统
