#!/usr/bin/env python
#encoding=utf-8

__metaclass__ = type

import commands
import re
import os

class Checker:
    def __init__(self, subchecker=[]):
        self.subchecker = subchecker
        self._checked_result = None
        pass

    def check(self):
        return all([x.result() for x in self.subchecker])

    def result(self):
        if self._checked_result == None:
            self._checked_result = self.check()
        return self._checked_result

    def custom_description(self):
        return (TrueChecker() if self.result() else FalseChecker()).description()

    def description(self):
        for checker in self.subchecker:
            if not checker.result():
                return checker.description()

        return str(
            SuccessHeaderDecorator(self.custom_description()) if self.result() else ErrorHeaderDecorator(self.custom_description())
        )

class TrueChecker(Checker):
    def check(self):
        return true

    def description(self):
        return SuccessTextDecorator("SUCCESS!!!")

class FalseChecker(Checker):
    def check(self):
        return ErrorTextDecorator("ERROR!!!")

class CommandChecker(Checker):
    def __init__(self, command, subchecker = []):
        super(CommandChecker, self).__init__(subchecker=subchecker)
        self.command = command
        self.status_and_output = None

    def command_validator(self):
        return self.status_and_output[0] == 0

    def check(self):
        if not super(CommandChecker, self).check():
            return false

        self.status_and_output = commands.getstatusoutput(self.command)
        return self.command_validator()

    def custom_description(self):
        return "%s 命令运行%s!" % (self.command, "成功" if self.result() else "失败")

class CommandInstalledChecker(CommandChecker):
    def __init__(self, command):
        super(CommandInstalledChecker, self).__init__(command="which %s" % command)
        self.original_command = command

    def custom_description(self):
        if self.result():
            return "命令 %s 已安装" % self.original_command
        else:
            return "命令 %s 未安装" % ErrorTextDecorator(self.original_command)

class CommandResultRangeChecker(CommandChecker):
    def __init__(self, command, valid_range = (-1, 1000), subchecker = []):
        super(CommandResultRangeChecker, self).__init__(command=command, subchecker=subchecker)
        self.command_int_result = 0
        self.valid_range = valid_range

    def command_validator(self):
        if not super(CommandResultRangeChecker, self).command_validator():
            return False

        self.command_int_result = int(self.status_and_output[1])

        return self.valid_range[0] <= self.command_int_result <= self.valid_range[1]

    def custom_description(self):
        if self.result():
            return "%s 命令的运行结果为 %i" % (self.command, self.command_int_result)
        else:
            return "%s 命令的运行结果为 %s" % (self.command, ErrorTextDecorator(self.command_int_result))
        
class MySQLConnectionNumberChecker(CommandResultRangeChecker):
    def __init__(self, valid_range = (300, float("inf"))):
        super(MySQLConnectionNumberChecker, self) \
            .__init__(command="lsof -i -n -P | grep TCP | grep '3306' | wc -l",
                      valid_range=valid_range,
                      subchecker=[
                          CommandChecker(command="which lsof 1>/dev/null || yum install lsof"),
                      ])

    def custom_description(self):
        if self.result():
            return "当前 MySQL 连接数为 %s" % self.command_int_result
        else:
            return "当前 MySQL 连接数为 %s" % ErrorTextDecorator(self.command_int_result)

class RedisConnectionNumberChecker(CommandResultRangeChecker):
    def __init__(self, valid_range = (300, float("inf"))):
        super(RedisConnectionNumberChecker, self) \
            .__init__(command="lsof -i -n -P | grep TCP | grep '6379' | wc -l",
                      valid_range=valid_range,
                      subchecker=[
                          CommandChecker(command="which lsof 1>/dev/null || yum install lsof"),
                      ])

    def custom_description(self):
        if self.result():
            return "当前 Redis 连接数为 %s" % self.command_int_result
        else:
            return "当前 Redis 连接数为 %s" % ErrorTextDecorator(self.command_int_result)

class NetworkDelayChecker(CommandChecker):
    def __init__(self, domain, count=10, valid_range=(0, 1000)):
        super(NetworkDelayChecker, self).__init__(command="ping %s -c %i | grep time=" % (domain, count))
        self.domain = domain
        self.count = count
        self.valid_range = valid_range
        self.avg_network_delay = -1.0

    def command_validator(self):
        if not super(NetworkDelayChecker, self).command_validator():
            return False

        def getTime(content):
            return float(re.sub(r".*time=((\d|\.)*).*", r"\1", content))

        outputs = str.split(self.status_and_output[1], "\n")
        times = [getTime(x) for x in outputs]

        self.avg_network_delay = sum(times) / len(times) if len(times) > 0 else float("inf")

        return self.valid_range[0] <= self.avg_network_delay <= self.valid_range[1]

    def custom_description(self):
        if self.result():
            return "%i 次 ping %s 的平均网络延迟为 %.2lfms" % (self.count, self.domain, self.avg_network_delay)
        else:
            return "%i 次 %s 的平均网络延迟为 %.2lfms" % (self.count, ErrorTextDecorator("ping %s" % self.domain), self.avg_network_delay)

class PathChecker(Checker):
    def __init__(self, path):
        super(PathChecker, self).__init__()
        self.path = path

    Checker.PATH_KEY = "path_checked_value"

    def check(self):
        return os.path.exists(self.path)

    def custom_description(self):
        if self.result():
            return "文件 %s 存在" % self.path
        else:
            return "文件 %s 不存在" % ErrorTextDecorator(self.path)

class CheckerConfiguration:
    @staticmethod
    def shared():
        try:
            return CheckerConfiguration._shared
        except AttributeError:
            CheckerConfiguration._shared = CheckerConfiguration()
            return CheckerConfiguration._shared

    def __init__(self):
        self.filenames_to_check = [
            "/usr/local/tomcat7/lib/tomcat-redis-session-manager-2.0.0.jar",
        ]

        self.domains_to_check = [
            # "baidu.com"
        ]

        self.command_checkers = [
            MySQLConnectionNumberChecker(),
            RedisConnectionNumberChecker(),
        ]

class TextDecorator:
    def __init__(self, component):
        self.component = component

    def __str__(self):
        return str(self.component)

class ErrorTextDecorator(TextDecorator):
    def __str__(self):
        return "\033[31m%s\033[0m" % super(ErrorTextDecorator, self).__str__()

class SuccessTextDecorator(TextDecorator):
    def __str__(self):
        return "\033[32m%s\033[0m" % super(SuccessTextDecorator, self).__str__()

class ErrorHeaderDecorator(TextDecorator):
    def __str__(self):
        return "%s️\t%s" % (ErrorTextDecorator("ERROR⚠"), super(ErrorHeaderDecorator, self).__str__())

class SuccessHeaderDecorator(TextDecorator):
    def __str__(self):
        return "%s\t%s" % (SuccessTextDecorator("SUCCESS✅"), super(SuccessHeaderDecorator, self).__str__())

class CheckerRoutine:
    @staticmethod
    def routine():
        configuration = CheckerConfiguration.shared()

        for x in configuration.filenames_to_check:
            checker = PathChecker(path=x)
            print(checker.description())

        for x in configuration.domains_to_check:
            checker = NetworkDelayChecker(x)
            print(checker.description())

        for checker in configuration.command_checkers:
            print(checker.description())

if __name__ == "__main__":
    CheckerRoutine.routine()



