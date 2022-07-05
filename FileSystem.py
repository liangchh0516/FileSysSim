from basic import AcquireLock, ReleaseLock, Decode, FileSystem, HELP_MSG
from core import Command, SysInit
from functools import wraps
from threading import Thread
from time import sleep
from os import system
import signal
import pickle


PATH = './'
SYS_SAVE_NAME = 'FileSysSim.pickle'
QUIT_FLAG = False


def running_in_thread(func):
    """将此装饰器应用到需要在子线程运行的函数上.函数在调用的时候会运行在单独的线程中"""
    @wraps(func)  # 复制原函数元信息
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

    return wrapper


@running_in_thread
def AutoSave(sys: FileSystem):
    """每10秒自动保存一次，退出时自动保存"""
    while True:
        for i in range(100):
            sleep(0.1)
            if QUIT_FLAG == 1:
                break
        if QUIT_FLAG == 1:
            SaveSys(sys)
            break
        SaveSys(sys)


def my_handler(signum, frame):
    QUIT()


def QUIT():
    global QUIT_FLAG
    QUIT_FLAG = True


# 设置相应信号处理的handler
signal.signal(signal.SIGINT, my_handler)  # 读取Ctrl+c信号


def SaveSys(sys: FileSystem):
    """将文件系统类保存"""
    AcquireLock()
    with open(PATH + SYS_SAVE_NAME, 'wb') as f:
        pickle.dump(sys, f)
    ReleaseLock()


def LoadSys() -> FileSystem:
    """加载文件系统类"""
    try:
        with open(PATH + SYS_SAVE_NAME, 'rb') as f:
            sys = pickle.load(f)
            return sys
    except FileNotFoundError:
        raise FileNotFoundError('未找到保存的文件系统')


def SysInitialization() -> FileSystem:
    """初始化文件系统"""
    try:
        return LoadSys()
    except FileNotFoundError as e:
        print(e.__str__(), '\n按下回车进入初始化系统')
        input()
        return SysInit()


def interactive(input_list: list, cmd: Command) -> bool:
    """初步筛查输入信息并调用对应函数"""
    # 查看帮助信息
    if input_list[0] == 'h':
        cmd.help()

    # 新建空文件
    elif input_list[0] == 'touch':
        if len(input_list) != 2:
            print('请输入正确的文件名')
            return False
        cmd.CreateObj(input_list[1])

    # 删除文件/目录
    elif input_list[0] == 'rm':
        if len(input_list) != 2:
            print('请输入正确的文件名')
            return False
        print(cmd.rm(input_list[1]))

    # 查看子目录和文件信息
    elif input_list[0] == 'ls':
        if len(input_list) > 2:
            print('请输入正确的路径名')
            return False
        if len(input_list) == 1:
            cmd.ls()
        else:
            cmd.ls(input_list[1])

    # 新建目录
    elif input_list[0] == 'mkdir':
        if len(input_list) != 2:
            print('请输入正确的目录名')
            return False
        cmd.CreateObj(input_list[1], 'dir')

    # 递归移除目录
    elif input_list[0] == 'rmdir':
        if len(input_list) != 2:
            print('请输入正确的目录名')
            return False
        print(cmd.rmdir(input_list[1]))

    # 进入 子目录/根目录
    elif input_list[0] == 'cd':
        # 指定路径目录
        if len(input_list) == 2:
            cmd.cd(input_list[1])
        # 根目录
        elif len(input_list) == 1:
            cmd.cd()
        # 非法
        else:
            print('请输入正确的目录名')
            return False

    # 输出/追加/覆盖 文件内容
    elif input_list[0] == 'cat':
        cmd.cat(input_list[1:])

    # 查看空间使用情况
    elif input_list[0] == 'disk':
        if len(input_list) != 1:
            print('非法输入')
            return False
        cmd.disk()

    # 退出
    elif input_list[0] == 'exit':
        return True

    return False


def main():
    """此文件系统的主函数，包括保存、交互等"""
    system("cls")
    sys_lch = SysInitialization()
    AutoSave(sys_lch)
    cmd = Command(sys_lch)
    system("cls")  # 进入系统前清屏

    print(HELP_MSG)
    cmd.help()
    print('\n   欢迎！\n')

    # 死循环执行交互
    while True:
        print(f"\033[32m{Decode(cmd.sys.CtDir.path)}\033[0m", '# ', end='')

        Input = input()
        Input_list = Input.split()

        # 判断输入情况
        if len(Input_list) == 0:
            continue
        if Input_list[0] not in cmd.command.keys():
            print('没有找到命令，输入 h 查看帮助')
            continue

        # 根据输入执行对应函数
        if interactive(Input_list, cmd):
            print('Bye!')
            sleep(1)
            QUIT()
            break


if __name__ == '__main__':
    try:
        main()
        system("cls")  # 退出系统时清屏
    except EOFError:
        print('\nKeyBoardInterrupt')
        QUIT()
