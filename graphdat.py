class Graphdat(object):
	def __init__(self):
		print("Graphdat.__init__")
		
	def __del__(self):
		print("Graphdat.__del__")
		self.term()
		
	def term(self):
		print("Graphdat.term")
		
	def store(self, method, uri, host, msec):
		print("Graphdat.store", method, uri, host, msec)
		