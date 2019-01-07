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
        self._description = None
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

        return self.custom_description()

class TrueChecker(Checker):
    def check(self):
        return true

    def description(self):
        return SuccessTextDecorator("SUCCESS!!!")

class FalseChecker(Checker):
    def check(self):
        return ErrorTextDecorator("FAILED!!!")

class CommandChecker(Checker):
    def __init__(self, command, subchecker = []):
        super(CommandOutputChecker, self).__init__(subchecker=subchecker)
        self.command = command
        self.status_and_output = None

    def command_validator(self):
        return self.status_and_output[0] == 0

    def check(self):
        if not super(CommandOutputChecker, self).check():
            return false

        self.status_and_output = commands.getstatusoutput(self.command)
        return self.command_validator()

class CommandInstallChecker(CommandChecker):
    def __init__(self, command):
        super(CommandInstallChecker, self).__init__(command="which %s" % command)

class NetworkDelayChecker(RangeChecker):
    def __init__(self, domain, count=10, valid_range=(0, 1000)):
        super(NetworkDelayChecker, self).__init__(valid_range=valid_range)
        self.domain = domain
        self.count = count
        self.valid_range = valid_range

    def drive(self):
        def getTime(content):
            return float(re.sub(r".*time=((\d|\.)*).*", r"\1", content))

        outputs = str.split(commands.getoutput("ping %s -c %i | grep time=" % (self.domain, self.count)), "\n")
        return [getTime(x) for x in outputs]

    def value_to_check(self):
        times = self.drive()
        return sum(times) / len(times) if len(times) else 0

    def check(self):
        result = super(NetworkDelayChecker, self).check()
        self.checked_info[Checker.NETWORK_DELAY_KEY] = self.checked_info[Checker.RANGE_KEY]
        return result

class PathChecker(Checker):
    def __init__(self, path):
        super(PathChecker, self).__init__()
        self.path = path

    Checker.PATH_KEY = "path_checked_value"

    def check(self):
        self.checked_info[Checker.PATH_KEY] = self.path
        return os.path.exists(self.path)

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
            "baidu.com"
        ]

        self.command_checkers = [
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
        return "%s️\t%s" % (ErrorTextDecorator("异常⚠"), super(ErrorHeaderDecorator, self).__str__())

class SuccessHeaderDecorator(TextDecorator):
    def __str__(self):
        return "%s\t%s" % (SuccessTextDecorator("正常✅"), super(SuccessHeaderDecorator, self).__str__())

class CheckerRoutine:
    @staticmethod
    def routine():
        configuration = CheckerConfiguration.shared()

        for x in configuration.filenames_to_check:
            checker = PathChecker(path=x)
            if checker.check():
                print(SuccessHeaderDecorator("文件 %s 存在" % SuccessTextDecorator(x)))
            else:
                print(ErrorHeaderDecorator("文件 %s 不存在" % ErrorTextDecorator(x)))

        for x in configuration.domains_to_check:
            checker = NetworkDelayChecker(x)
            if checker.check():
                print(SuccessHeaderDecorator("ping %s 的延迟为 %.2lfms" % (x, checker.checked_info[Checker.NETWORK_DELAY_KEY])))
            else:
                print(ErrorHeaderDecorator("%s %s 的延迟为 %.2lfms 延迟较大" % (ErrorTextDecorator("ping"), ErrorTextDecorator(x), checker.checked_info[Checker.NETWORK_DELAY_KEY])))

if __name__ == "__main__":
    CheckerRoutine.routine()



