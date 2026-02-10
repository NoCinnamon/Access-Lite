import datetime

id = [2601, 2602, 2603, 2604]
firstName = ['Jiaqi', 'B', 'C', 'D']
lastNmae = ['liu', 'E', 'F', 'G']

x = str(datetime.datetime.now())
i = 3
attendanceRecord = "\n" + str(id[i]) + ' ' + firstName[i] + ' ' + lastNmae[i] + ' ' + x

print(attendanceRecord)
file = open("./data-file/helperAttendance.txt", "a")
file.write(attendanceRecord)
file.close()