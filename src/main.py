import imaplib
import sys
import os
import time
import threading
import zlib 

username = sys.argv[1]
password = sys.argv[2]
if not len(sys.argv) == 3:
    mailbox = sys.argv[3]
else: mailbox = False

conn = imaplib.IMAP4_SSL("imap.gmail.com")
conn.login(username, password)

if not mailbox:
    mailbox_list = conn.list()[1]
    for mbox in mailbox_list:
        print mbox.split(" ")
    mailbox = raw_input("Select mailbox: ")

r = conn.select(mailbox)
if not r[0] == "OK":
    print "Failed: %s"%str(r)
print "%s messages found"%r[1][0]
print "Grabbing this shit"

if not os.path.exists(username):
    os.mkdir(username)
if not os.path.exists(os.path.join(username,mailbox.replace("/","-"))):
    os.mkdir(os.path.join(username,mailbox.replace("/","-")))
p = os.path.join(username,mailbox.replace("/","-"))
_, data = conn.search(None,"ALL")

in_queue = []
threads = []
fails = []
def get_message():
    print "Thread started"
    connt = imaplib.IMAP4_SSL("imap.gmail.com")
    connt.login(username, password)
    connt.select(mailbox)
    print "Thread connected"
    while True:
        try:
            id = in_queue.pop()
        except Exception:
            print "Completed"
            return
        t1 = time.time()
        _, msg = connt.fetch(id, '(RFC822)')
        net_time = round(time.time()-t1,5)
        try:
            try:
                t2 = time.time()
                compressed_data = zlib.compress(msg[0][1],zlib.Z_BEST_COMPRESSION)
                comp_time = round(time.time()-t2,5)
                del msg
                t3 = time.time()
                x = open(os.path.join(p,id),"w")
                x.write(compressed_data)
                file_time = round(time.time()-t3,5)
                del compressed_data
                x.close()
            except Exception,e:
                print "Error with %s: %s"%(id, e)
                continue
            print "Done %s in %s (comp:%s net:%s io:%s)"%(id, str(time.time()-t1), 
                                                          comp_time, net_time, file_time)
        except Exception:
            fails.append(id)
            print "%s failed"%id
        

for number in data[0].split(" "):
    in_queue.append(number)
    
for x in xrange(5):
    t = threading.Thread(target=get_message)
    t.start()
    threads.append(t)

for thread in threads:
    thread.join()

x = open("failed")
for failed in fails:
    x.write(failed+"\n")
x.close()