from __future__ import annotations
from basic import File, Dir, FileSystem, FillStr, Encode, Decode, HELP_MSG


NAME_SIZE_LIMIT = 8


class Command:
    """用户操作集成为一个类"""
    command = {
        'h': '查看帮助',
        'touch': '新建一个空的文件并命名',
        'rm': '删除某个文件或目录',
        'ls': '查看当前目录下文件和目录',
        'mkdir': '新建目录',
        'rmdir': '移除目录',
        'cd': '进入某个子目录 或 回到根目录',
        'cat': '输出/追加/覆盖 文件内容',
        'disk': '查看磁盘剩余空间',
        'exit': '退出系统'
    }

    def __init__(self, sys: FileSystem):
        self.sys = sys

    def help(self):
        """输出帮助信息"""
        print("本系统包含以下基本命令：")
        print('\n'.join([FillStr(s, 6, ' ') + ': ' + self.command[s] for s in self.command.keys()]))

    def CreateObj(self, path: str, obj_type: str = 'file' or 'dir') -> None:
        """新建一个子对象并命名，默认创建文件"""

        StartDir, f_path, t_path = AnalysisPath(self.sys, path)
        name_bin = Encode(t_path[-1])

        try:
            TargetFather = GetObjFromPath(StartDir, f_path)
        except Exception as e:
            print('/'.join(f_path) + ':' + e.__str__())
            return

        try:
            CheckInput(self.sys.CtDir, Encode(t_path[-1]))
        except Exception as e:
            print(t_path[-1] + ':' + e.__str__())
            return

        if obj_type == 'file':
            # 创建文件
            TargetFather.son.append(File(name_bin, TargetFather.path + b'/' + name_bin))
        elif obj_type == 'dir':
            # 创建目录
            TargetFather.son.append(Dir(name_bin, TargetFather.path + b'/' + name_bin, TargetFather))

    def rm(self, path: str) -> str:
        """删除某个文件或目录"""
        try:
            TargetFather, Target = GetTarget(self.sys, path)
        except Exception as e:
            return path + e.__str__()

        return remove(self.sys, TargetFather, Target)

    def ls(self, path: str = None) -> None:
        """查看目录下文件和目录"""
        # 查看当前目录
        if path is None:
            Target = self.sys.CtDir
        # 查看指定目录
        else:
            try:
                _, Target = GetTarget(self.sys, path)
            except Exception as e:
                print(path + ':' + e.__str__())
                return

        if Target.type == b'file':
            print(path + ':' + '是一个文件')

        print('-权限-  --名称--  -----最近修改时间-----  --大小--')
        for obj in Target.son:
            # 目录，直接输出
            if obj.type == b'dir':
                print('d---    ' + FillStr(Decode(obj.name), 8, ' ', 0))

        for obj in Target.son:
            # 文件，输出权限 + 名称 + 最后修改时间
            if obj.type == b'file':
                print('-' + FillStr(File.FilePower[obj.power], 7, ' ')
                      + FillStr(Decode(obj.name), 8, ' ', 0)
                      + FillStr(Decode(obj.LastTime), 23, ' ', 0)
                      + FillStr(str(obj.size), 10, ' ', 0)
                      + 'B')

    def rmdir(self, path: str) -> str:
        """递归删除当前目录的一个子目录"""

        print(f'这个操作将删除目录 {path} 以及此目录下的所有文件和目录，是否继续？\n'
              'y or Y -> 继续；其他 -> 退出', end=':')
        flag = input()
        if flag.lower() != 'y':
            return '退出删除操作'

        # 找到要递归删除的目录
        try:
            TargetFather, Target = GetTarget(self.sys, path)
        except Exception as e:
            return path + ':' + e.__str__()

        if Target.type == b'file':
            return path + ':' + '是一个文件'

        print(' '.join(['删除' + path + '开始']), end='\n\n')
        # 采用压栈出栈的方式遍历全部子目录和子目录中的文件
        # 后序遍历，即 子节点1 -> 子节点2 -> ... -> 子节点n -> 根节点
        stack = [Target]
        while len(stack) > 0:
            trans_root = stack[len(stack) - 1]

            # 取出了所有子目录和子文件，出栈
            if len(trans_root.son) == 0:
                print(remove(self.sys, trans_root.father, trans_root))
                stack.remove(trans_root)
                continue

            # 对子目录的子文件/目录
            for obj in trans_root.son:
                # 文件，删除
                if obj.type == b'file':
                    print(remove(self.sys, trans_root, obj))
                # 目录，压栈
                else:
                    stack.append(obj)
                    break

        self.sys.CtDir = TargetFather
        return '\n' + ' '.join(['删除', path, '完成'])

    def cd(self, path: str = None) -> None:
        """进入某个目录"""
        # 为空，进入根目录
        if path is None:
            self.sys.CtDir = self.sys.RootDir
            return

        # 为b'..'，进入父目录
        if path == b'..':
            self.sys.CtDir = self.sys.CtDir.father
            return

        # 指定路径时
        try:
            _, Target = GetTarget(self.sys, path)
        except Exception as e:
            print(path + ':' + e.__str__())
            return

        if Target.type == b'file':
            print(path + ':' + '是一个文件')
            return

        self.sys.CtDir = Target

    def cat(self, param_list: list):
        """查看/覆盖/追加 文件内容"""
        # 覆盖或追加
        if len(param_list) == 3:
            try:
                # 覆盖
                if param_list[1] == ">":
                    cat(self.sys, 'cover', param_list[2], param_list[0])
                # 追加
                elif param_list[1] == ">>":
                    cat(self.sys, 'add', param_list[2], param_list[0])
                else:
                    print('非法输入')
            except Exception as e:
                print(param_list[2] + ':' + e.__str__())

        # 查看文件内容
        elif len(param_list) == 1:
            try:
                print(cat(self.sys, 'read', param_list[0]))
            except Exception as e:
                print(param_list[0] + ':' + e.__str__())
        else:
            print('非法输入')

    def disk(self) -> None:
        """查看存储空间使用情况"""
        used, remain = self.sys.Disk()
        print(f'空间使用了{str(used * 100)}%，剩余{remain}KB')


def CheckInput(tg_dir: Dir, name_bin: bytes) -> str:
    """检查输入合法性 以及 是否有重名对象"""
    # 检查输入合法性
    if len(name_bin) > NAME_SIZE_LIMIT:
        raise Exception('文件名过长')
    # 检查在同一目录是否有同名子节点
    try:
        tg_dir.FindSon(name_bin)
    except Exception as e:
        return e.__str__()
    raise Exception('存在同名目录/文件')


def SysInit():
    """使用此方法初始化文件系统"""
    sys = FileSystem()
    cmd = Command(sys)
    cmd.CreateObj('root', 'dir')
    cmd.cd('root')
    cmd.CreateObj('message')
    cmd.cat([HELP_MSG, '>', 'message'])
    cmd.CreateObj('testDir', 'dir')
    cmd.cd('testDir')
    cmd.CreateObj('file1')
    cmd.cat(['This is a test file.', '>', 'file1'])
    cmd.CreateObj('BigFile')
    cmd.cat(['1234567890' * 1000, '>', 'BigFile'])
    cmd.CreateObj('dir1', 'dir')
    cmd.cd('..')
    return sys


def AnalysisPath(sys: FileSystem, path: str = None) -> (Dir, list, list):
    """根据输入的字符串找到父路径以及当前路径"""
    # 根目录
    if path.startswith('/'):
        # 会切一个空字符串出来
        path = path.split('/')[1:]
        return sys.RootDir, path[:-1], path

    # 当前目录
    return sys.CtDir, path.split('/')[:-1], path.split('/')


def GetObjFromPath(str_dir: Dir, path: list) -> (Dir | File):
    """根据起始目录和输入路径找到目标目录/文件"""
    ViaObj = str_dir

    # 逐层深入
    for ViaDirName in path:
        if ViaDirName == '..':
            if ViaObj.father is None:
                continue
            ViaObj = ViaObj.father
            continue

        ViaObj = ViaObj.FindSon(Encode(ViaDirName))

    return ViaObj


def GetTarget(sys: FileSystem, path: str) -> (Dir, Dir | File):
    """从输入的路径判断目标路径"""
    StartDir, f_path, t_path = AnalysisPath(sys, path)
    TargetFather = GetObjFromPath(StartDir, f_path)
    Target = GetObjFromPath(StartDir, t_path)

    return TargetFather, Target


def cat(sys: FileSystem, *args: str) -> str:
    """cat每种逻辑的操作"""
    # 找到文件
    _, Target = GetTarget(sys, args[1])

    if Target.type == b'dir':
        raise Exception('是一个目录')

    if args[0] == 'read':
        # 查看
        return Decode(sys.Read(Target.address))
    elif args[0] == 'cover':
        # 覆盖
        sys.Delete(Target.address)
        Target.Write(sys.Write(Encode(args[2])), len(Encode(args[2])))
    elif args[0] == 'add':
        # 追加
        str_old = sys.Read(Target.address)
        sys.Delete(Target.address)
        Target.Write(sys.Write(str_old + Encode(args[2])), len(str_old + Encode(args[2])))
    else:
        raise Exception('系统错误！')


def remove(sys: FileSystem, target_father: Dir, target: Dir | File):
    """删除指定目录下的指定文件/目录"""
    # 文件
    if target.type == b'file':
        # 删除存储信息
        sys.Delete(target.address)
    # 目录，且不为空
    elif len(target.son) != 0:
        return '目录不为空，尝试使用命令 rmdir ' + Decode(target.name)

    target_father.DelSon(target)

    return ' '.join(['删除' + Decode(target.name) + '成功'])


def SpiltLine():
    print('---------------------------------')


def Test():
    # 这是一个函数测试用例
    sys_lch = FileSystem()
    cmd_lch = Command(sys_lch)
    SpiltLine()
    cmd_lch.disk()
    SpiltLine()
    cmd_lch.CreateObj('dir1', 'dir')
    cmd_lch.CreateObj('file1')
    cmd_lch.CreateObj('dir2', 'dir')
    cmd_lch.ls()
    SpiltLine()
    cmd_lch.cd('dir1')
    cmd_lch.CreateObj('file1')
    cmd_lch.ls()
    SpiltLine()
    cmd_lch.CreateObj('file2')
    cmd_lch.cat(['111', '>>', 'file2'])
    cmd_lch.cat(['file2'])
    SpiltLine()
    cmd_lch.cat(['222', '>>', 'file2'])
    cmd_lch.cat(['file2'])
    SpiltLine()
    cmd_lch.cat(['333', '>', 'file2'])
    cmd_lch.cat(['file2'])
    SpiltLine()
    print(cmd_lch.rm('file2'))
    SpiltLine()
    cmd_lch.disk()
    SpiltLine()
    cmd_lch.CreateObj('ddd', 'dir')
    cmd_lch.cd('dir2')
    cmd_lch.CreateObj('file3')
    cmd_lch.cd('..')
    cmd_lch.cd()
    print(cmd_lch.rmdir('dir1'))
    SpiltLine()


if __name__ == '__main__':
    print('运行此文件用于测试所有用户级操作函数')
    Test()
