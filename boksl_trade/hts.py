from pywinauto import application
import time
import os


def restart():
    """크래온플러스를 다시 시작함"""

    ##################################################
    # 사용자 아이디, 비밀번호, 공동인증비밀번호
    userid = ""
    pwd = ""
    pwdcert = ""
    ##################################################

    # 기존 크래온플러스를 종료
    print("재시작 - 크래온 PLUS 종료")
    os.system("taskkill /IM coStarter* /F /T")
    os.system("taskkill /IM CpStart* /F /T")
    os.system("taskkill /IM DibServer* /F /T")
    os.system("wmic process where \"name like '%coStarter%'\" call terminate")
    os.system("wmic process where \"name like '%CpStart%'\" call terminate")
    os.system("wmic process where \"name like '%DibServer%'\" call terminate")
    time.sleep(10)

    # 새롭게 시작
    print("재시작 - 크래온 PLUS 실행")
    app = application.Application()
    command = "C:\CREON\STARTER\coStarter.exe /prj:cp /id:{} /pwd:{} /pwdcert:{} /autostart".format(userid, pwd, pwdcert)
    app.start(command)
    time.sleep(60)


if __name__ == "__main__":
    restart()
