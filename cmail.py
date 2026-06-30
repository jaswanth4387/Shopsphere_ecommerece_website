import smtplib
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('jaswanthjakkampudi438@gmail.com','qnfh dren fafq fegp')
    msg=EmailMessage()
    msg['FROM']='jaswanthjakkampudi438@gmail.com'
    msg['SUBJECT']=subject
    msg['TO']=to
    msg.set_content(body)
    server.send_message(msg)
    server.close()
    


