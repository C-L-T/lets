import string
import random
from datetime import datetime
import time

def randomString(length = 8):
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def stringToBool(s):
	"""
	Convert a string (True/true/1) to bool

	s -- string/int value
	return -- True/False
	"""
	return (s == "True" or s== "true" or s == "1" or s == 1)

def osuDateToUNIXTimestamp(osuDate):
	"""
	Convert an osu date to UNIX date

	osuDate -- osudate
	"""
	date_object = datetime.strptime(osuDate, "%y%m%d%H%M%S")
	unixtime = time.mktime(date_object.timetuple())
	unixtime = int(unixtime)
	return unixtime
