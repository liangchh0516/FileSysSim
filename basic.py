from __future__ import annotations
import time
import math
import threading

# 64 * 1024个块，一个块大小为256B，总共16MB
BLOCK_AMT = 64 * 1024 - 2
BLOCK_SIZE = 256

# 64 * 1024个块只需 16位来标识，这里使用FAT16(16位FAT）
# 0x0000            未分配
# 0x0001 ~ 0xFFFE   已分配
# 0xFFFF            文件结束符
# 舍去了 第一块(0x0000），最后一块(0xFFFF)
BLOCK_STR = 1
BLOCK_END = 0xFFFE
FAT_END_FLAG = 'FFFF'
FAT_ENTRY_SIZE = 4

HELP_MSG = f"这是 操作系统课程设计实验课 试验11 的 模拟文件系统\n" \
           f"使用位示图管理内存空间，FAT表记录文件映射\n" \
           f"每一个块大小为{BLOCK_SIZE}B，有{BLOCK_AMT}个块，总共{round((BLOCK_SIZE * BLOCK_AMT) / (1024 * 1024), 2)}M大小"

# 写锁
# 请求 .acquire()
# 释放 .release()
WriteLock = threading.Lock()


class FAT:
    """
    创建FAT表，包括方法:
        AddEntry -> 增加表项\n
        AddEndFlag -> 增加文件结束标志\n
        ReadEntry -> 从指定位置读取表项\n
        DelEntry -> 从指定位置删除表项
    """

    def __init__(self):
        self.FAT = FAT_END_FLAG

    def AddEntry(self, s: str) -> None:
        """在表的末尾添加表项"""
        self.FAT += FillStr(s, 4, '0', 0)

    def AddEndFlag(self) -> None:
        """在表的末尾添加结束标志"""
        self.FAT += FAT_END_FLAG

    def ReadEntry(self, place: int) -> str:
        """读取指定位置表项"""
        return self.FAT[place: place + FAT_ENTRY_SIZE]

    def DelEntry(self, place: int) -> None:
        """删除指定位置表项"""
        self.FAT = self.FAT[: place] + self.FAT[place + 4:]


class BitMap:
    """
    创建位示图，包括方法：
        GetEmptyBlock -> 获得一个盘块为空的盘块号\n
        EmptyBlockAMT -> 获得所有为空的盘块数\n
        Write -> 写入指定盘块位示图\n
        Read -> 读取指定盘块位示图\n
    """

    def __init__(self):
        self.BitMap = {i: 0 for i in range(BLOCK_STR, BLOCK_END + 1)}

    def GetEmptyBlock(self) -> int:
        """
        每次找到一个空闲的块，并返回块号\n
        若没有空闲的块则返回 -1
        """
        if 0 not in self.BitMap.values():
            return -1

        for i in range(BLOCK_STR, BLOCK_END + 1):
            if self.BitMap[i] == 0:
                return i

    def EmptyBlockAMT(self) -> int:
        """返回空闲盘块的数量"""
        return list(self.BitMap.values()).count(0)

    def Write(self, block_num: int, bit: int = 0 or 1) -> None:
        """写入指定盘块位示图"""
        self.BitMap[block_num] = bit

    def Read(self, block_num: int) -> int:
        """读取指定盘块位示图"""
        return self.BitMap[block_num]


class Storage:
    """
    虚拟存储空间的创建，包括方法：
        Write -> 将指定数据写入指定盘块号中\n
        Read -> 读取指定盘块号数据\n
    """

    def __init__(self):
        self.Storage = {i: b'' for i in range(BLOCK_STR, BLOCK_END + 1)}

    def Write(self, block_num: int, data: bytes) -> None:
        """将数据写入指定盘块号中"""
        self.Storage[block_num] = data

    def Read(self, block_num: int) -> bytes:
        """读取指定盘块号数据"""
        return self.Storage[block_num]


class Dir:
    """
    创建一个新的目录，包括

    属性：
        name(bytes) -> 目录名\n
        father(Dir) -> 父目录\n
        path(byte) -> 目录路径\n
        son(Dir) -> 子目录/文件\n
        CreateTime(byte) -> 创建文件的时间\n
        type(bytes) -> 类型\n

    方法：
        FindSonFather -> 指定父目录\n
        AddSon -> 添加子目录\n
        DelSon -> 删除指定子目录/文件的映射关系\n
    """

    def __init__(self, dirname: bytes, path: bytes, father: Dir = None):
        self.name = dirname
        self.father = father
        self.son = []
        self.path = path
        self.CreateTime = GetCurrentTime()
        self.type = b'dir'

    def AddSon(self, other: (Dir | File)) -> None:
        """增加此目录下文件或目录"""
        self.son.append(other)

    def DelSon(self, obj: (Dir | File)) -> None:
        """此目录下文件或目录的映射关系"""
        self.son.remove(obj)

    def FindSon(self, name_bin: bytes) -> (File | Dir):
        """找到此目录中是否有某个名字的子目录/子文件"""
        for elm in self.son:
            if elm.name == name_bin:
                return elm

        raise Exception('没有那个文件或目录')


class File:
    """
    文件的类（union表），包括

    属性：
        name(int) -> 文件名\n
        power(int) -> 文件权限\n
        size(int) -> 文件大小\n
        path(byte) -> 文件路径\n
        LastTime(str) -> 最后修改时间\n
        address(str) -> 内存储存首盘块号\n
        type(byte) -> 文件类型
    方法：
        Write -> 写入\n
        ChangeFilePower -> 修改权限
    """
    FilePower = {1: 'r--', 2: 'w--', 3: 'rw-', 4: '--x', 5: 'r-x', 6: '-wx', 7: 'rwx'}

    def __init__(self, filename: bytes, path: bytes):
        self.name = filename
        self.address = None
        self.LastTime = GetCurrentTime()
        self.path = path
        self.power = 3
        self.size = 0
        self.type = Encode('file')

    def Write(self, address: int, size: int):
        """记录写入首盘块地址、写入时间"""
        self.address = FillStr(IntToHexStr(address), 4, '0', 0)
        self.LastTime = GetCurrentTime()
        self.size = size

    def ChangeFilePower(self, power: int):
        """修改文件权限为power"""
        # 保证输入的正确性
        if power not in self.FilePower.keys():
            print(f'请输入正确的数字:{self.FilePower.keys()}')
            return

        self.power = power


class User:
    """用户，暂未开发"""
    def __init__(self, usr_name: bytes):
        self.UsrName = usr_name
        self.PassWd = ''


class FileSystem:
    """
    创建文件系统，包括

    属性：
        BitMap(BitMap) -> 位示图\n
        Storage（Storage） -> 存储空间\n
        FAT（FAT） -> FAT表\n
        RootDir(Dir) -> 根目录\n
        CtDir(Dir) -> 当前目录\n
        CtUsr(User) -> 暂未开发\n
    方法：
        Write -> 写入指定数据\n
        Read -> 根据FAT表读取盘块中内容\n
        Delete -> 根据输入的盘块号删除存储空间中内容\n
        Disk -> 获得存储空间使用量、剩余空间大小
    """

    def __init__(self):
        """文件系统初始化"""
        self.BitMap = BitMap()  # 创建位示图
        self.Storage = Storage()  # 创建存储
        self.FAT = FAT()  # 创建FAT表
        self.CtUser = User(b'root')  # 创建当前用户
        self.RootDir = Dir(b'home', b'', None)  # 创建根目录
        self.CtDir = self.RootDir  # 当前目录

    def Write(self, data: bytes) -> int:
        """
        写入指定数据，返回写入的第一个盘块号

        若盘块数不足则返回-1，写入出错返回0
        :param data: 要写入的数据
        :return: 写入的第一个盘块号
        """
        # 计算需要的盘块数
        BlockAmt = math.ceil(len(data) / BLOCK_SIZE)

        # 判断剩下的盘块是否够用
        if BlockAmt > self.BitMap.EmptyBlockAMT():
            return -1

        # 分盘块写入数据，不满一块算占一块盘块
        # 一个文件的写入是一个不可分的操作，需要写锁
        AcquireLock()

        FirstWrite = 0
        for WriteRank in range(BlockAmt):
            BlockNum = self.BitMap.GetEmptyBlock()

            # 写入数据
            self.Storage.Write(BlockNum, data[WriteRank * BLOCK_SIZE:] if WriteRank == BlockAmt - 1 else data[WriteRank * BLOCK_SIZE: (WriteRank + 1) * BLOCK_SIZE])
            # 将位示图对应标签置1
            self.BitMap.Write(BlockNum, 1)
            # 更新FAT表
            self.FAT.AddEntry(IntToHexStr(BlockNum))

            # 找到首个写入盘块的盘块号
            if WriteRank == 0:
                FirstWrite = BlockNum

        # 增加结束标志
        self.FAT.AddEndFlag()

        ReleaseLock()

        # 返回第一个存储盘块号
        return FirstWrite

    def Read(self, first_block: str) -> bytes:
        """
        根据输入的首盘块号开始读取 FAT 表，直到读到 ’FFFF‘

        :param first_block: 首盘块号
        :return: 读取的文件内容
        """
        # 找到目标表项
        place = 0
        while self.FAT.ReadEntry(place) != first_block:
            # 没找到
            if place == len(self.FAT.FAT) - 4:
                return b''
            place += FAT_ENTRY_SIZE

        # 读取文件内容
        data_bin = b''
        while True:
            StoragePlace = HexStrToInt(self.FAT.ReadEntry(place))

            # 读到了结束符
            if StoragePlace == HexStrToInt(FAT_END_FLAG):
                return data_bin

            # 连接二进制数据
            data_bin += self.Storage.Read(StoragePlace)
            place += FAT_ENTRY_SIZE

    def Delete(self, first_block: str) -> bool:
        """根据输入的首盘块号删除对应文件内容"""

        # 找到盘块号
        place = 0
        while self.FAT.ReadEntry(place) != first_block:
            # 没找到
            if place == len(self.FAT.FAT):
                return False
            place += FAT_ENTRY_SIZE

        # 删除为原子操作，申请写锁
        AcquireLock()

        # 删除
        while self.FAT.ReadEntry(place) != FAT_END_FLAG:
            BlockNum = HexStrToInt(self.FAT.ReadEntry(place))

            # 删除FAT表
            self.FAT.DelEntry(place)
            # 将位示图对应标签置0
            self.BitMap.Write(BlockNum, 0)
            # 删除数据（此处是否更改sys.Storage对结果没有影响）
            self.Storage.Write(BlockNum, b'')

        # 删除FAT表结束标志
        self.FAT.DelEntry(place)

        ReleaseLock()
        return True

    def Disk(self) -> (float, float):
        """返回存储空间使用量，剩余空间大小（KB）"""
        return round((1 - (self.BitMap.EmptyBlockAMT() / (BLOCK_END - BLOCK_STR + 1))), 4), self.BitMap.EmptyBlockAMT() / 4


def IntToHexStr(num: int) -> str:
    """将输入的整形数字转换为16进制字符串"""
    return hex(num)[2:].upper()


def HexStrToInt(s: str) -> int:
    """将输入的16进制字符串转换为整形数字"""
    return int(s, 16)


def Encode(s: str) -> bytes:
    """返回字符串UTF-8编码"""
    # 例：'你aa'.encode('utf-8') = b'\xe4\xbd\xa0aa' 占5字节
    return s.encode('utf-8')


def Decode(binary: bytes) -> str:
    """返回二进制对应UTF-8编码字符串"""
    return binary.decode()


def GetCurrentTime() -> bytes:
    """返回当前时间"""
    current_time = time.localtime()
    return Encode(time.strftime("%Y-%m-%d %H:%M:%S", current_time))


def AcquireLock():
    """请求锁"""
    WriteLock.acquire()


def ReleaseLock():
    """释放锁"""
    WriteLock.release()


def FillStr(str1: str, length: int, str2: str, flag=1) -> str:
    """用str2填充str1至length，默认从后填充，flag=0从前填充"""
    n = math.ceil((length - len(str1)) / len(str2))
    if flag == 1:
        NewStr = str1 + str2 * n
        return NewStr[:length]
    NewStr = str2 * n + str1
    return NewStr[-length:]
