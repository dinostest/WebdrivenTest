from optparse import OptionParser
import imaplib
import sys

print sys.argv

usage = "usage: %prog [options]"

parser = OptionParser(usage)

parser.add_option("-a","--action",dest="action", help="delete or unread the email")
parser.add_option("-s","--server",dest="server", help="mail server to be operated")
parser.add_option("-u","--user",dest="username", help="username for mailbox")
parser.add_option("-p","--password",dest="password", help="password for mailbox")
parser.add_option("-b","--batchid",dest="batchid", help="batchid to be operated")

(options,args) = parser.parse_args()


if not (options.server and options.action and options.username and options.password and options.batchid):
	parser.print_help()
	sys.exit(0)

M = imaplib.IMAP4_SSL(options.server)
M.login(options.username,options.password)
M.select()
if options.action == "empty":
	typ,data=M.search(None,'ALL')
	for num in data[0].split():
		M.store(num,'+FLAGS','\\Deleted')
	M.expunge()
else:
	typ,data=M.search(None,'SUBJECT',options.batchid)
	if options.action == "remove":
		for num in data[0].split():
			M.store(num,'+FLAGS','\\Deleted')
		M.expunge()
	elif options.action == "unread":
		for num in data[0].split():
			M.store(num,'-FLAGS','\\Seen')
	else:
		print "%prog only supports remove, empty, and unread options currently"
	