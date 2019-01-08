#!/usr/bin/env python
#encoding=utf-8
# Author: 高炼
# Date: 2019-01-08

__metaclass__ = type

import commands
from precondition import *

class CheckDirectorRoutine:
    @staticmethod
    def exec_python_script_in_container(container_id, source):
        return commands.getstatusoutput("$s | docker exec --interactive %s python" % (source, container_id))

    @staticmethod
    def routine():
        checker = CommandChecker(command="docker ps 2>/dev/null")
        if not checker.result():
            exit(1)

        docker_container_id_names = str.split(commands.getoutput('docker ps --filter "name=hwsc" --format "{{.ID}}\t{{.Names}}"'), "\n")
        docker_container_id_names = map(lambda _ : str.split(_, "\t"), docker_container_id_names)

        if len(docker_container_id_names):
            print(SuccessTextDecorator("共查询到 %s 个容器信息，开始执行脚本...\n"))

        for container_id, name in docker_container_id_names:
            print(SuccessTextDecorator("开始检查容器 %s(%s)..." % (name, container_id)))
            status, output = CheckDirectorRoutine.exec_python_script_in_container(
                container_id,
                "curl -s https://raw.githubusercontent.com/mangonob/check_director/master/precondition.py"
            )

            if status == 0:
                print(output)
                print(SuccessTextDecorator("容器 %s(%s) 检查完毕!!!\n" % (name, container_id)))
            else:
                print(SuccessTextDecorator(ErrorTextDecorator(output)))

if __name__ == "__main__":
    CheckDirectorRoutine.routine()
