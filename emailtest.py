import smtplib

message = """From: Charles Xavier <iotgroup14@gmail.com>
To: JAMES <jco2127@columbia.edu>
Subject: Burner Left On

You left your stove on, idiot!
"""

try:
   smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
   smtpObj.starttls()
   smtpObj.login('iotgroup14', 'P@$sw0rd1234')
   smtpObj.sendmail('iotgroup14@gmail.com', ['jco2127@columbia.edu'], message)
   smtpObj.quit()         
   print "Successfully sent email"
except Exception:
   print "Error: unable to send email"
