import csv


csv_filename = "employee-log.csv"

headers = ['ID', 'First Name', 'Last Name', 'File Name', 'Status']

with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    
    writer.writerow(headers)
    
    # Example: Adding one row of data
    # You can replace these with your variables from the face recognition loop
    writer.writerow([2600, 'Jiaqi', '01', './jiaqi/jiaqi-1.jpg', 'Authorized'])
    writer.writerow([2601, 'Jiaqi', '02', './jiaqi/jiaqi-2.JPG', 'Authorized'])
    writer.writerow([2602, 'Jiaqi', '03', './jiaqi/jiaqi-3.jpeg', 'Authorized'])
    writer.writerow([2603, 'Jiaqi', '04', './jiaqi/jiaqi-4.jpeg', 'Authorized'])
    writer.writerow([2604, 'Jiaqi', '05', './jiaqi/jiaqi-5.jpeg', 'Authorized'])
    writer.writerow([2605, 'Jiaqi', '07', './jiaqi/jiaqi-7.jpeg', 'Authorized'])

    writer.writerow([2606, 'Adele', '01', './Adele/Adele-00.webp', 'Authorized'])
    writer.writerow([2607, 'Adele', '02', './Adele/Adele-01.webp', 'Authorized'])
    writer.writerow([2608, 'Adele', '03', './Adele/Adele-02.webp', 'Authorized'])
    writer.writerow([2609, 'Adele', '04', './Adele/Adele-03.webp', 'Authorized'])

    writer.writerow([2610, 'Taylor', '01', './Taylor Swift/Taylor-00.webp', 'Authorized'])
    writer.writerow([2611, 'Taylor', '02', './Taylor Swift/Taylor-01.webp', 'Authorized'])
    writer.writerow([2612, 'Taylor', '03', './Taylor Swift/Taylor-02.webp', 'Authorized'])
    writer.writerow([2613, 'Taylor', '04', './Taylor Swift/Taylor-03.webp', 'Authorized'])
    writer.writerow([2614, 'Taylor', '05', './Taylor Swift/Taylor-06.jpg', 'Authorized'])

    writer.writerow([2615, 'He', 'Zhang', './ZhangHe/zhanghe-1.jpeg', 'Authorized'])
    writer.writerow([2616, 'Miranda', 'Kerr', './Miranda Kerr/kerr-1.jpeg', 'Authorized'])
    writer.writerow([2617, 'J', 'Phonex', './JPhonex/JP-01.webp', 'Authorized'])
    writer.writerow([2618, 'M', 'Mountain', './red-list/Mountain.jpg', 'Denied'])
    writer.writerow([2619, 'Isreal', 'Keyes', './red-list/Isreal-Keyes.jpg', 'Denied'])

print(f"File '{csv_filename}'Created succefully.")
