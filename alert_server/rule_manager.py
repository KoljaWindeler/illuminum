__author__ = 'kolja'

# wir brauchen eine liste die
# data[0].account
# data[0].area[0].area
# data[0].area[0].next_time_based_action
# data[0].area[0].rules[0].id
# data[0].area[0].rules[0].connector
# data[0].area[0].rules[0].arg1
# data[0].area[0].rules[0].arg2
# data[0].area[0].sub_rules[0].id
# data[0].area[0].sub_rules[0].connector
# data[0].area[0].sub_rules[0].arg1
# data[0].area[0].sub_rules[0].arg2
# data[0].area[0].reload_rules()
# data[0].area[0].check_rules()
# data[0].area[0].eval_rule(conn,arg1,arg2)->true/false
# data[0].area[0].get_sub_rule(sub_rule_id)->(con,arg1,arg2)

class rule:
	def __init__(self, id, conn, arg1, arg2):
		self.id = id
		self.conn = conn
		self.arg1 = arg1
		self.arg2 = arg2

class area:
	def __init__(self,name):
		self.name = name
		self.rules = []
		self.sub_rules = []

	def add_sub_rule(self, id, conn, arg1, arg2):
		self.sub_rules.append(rule(id,conn,arg1,arg2))

	def add_rule(self, id, conn, arg1, arg2):
		self.rules.append(rule(id,conn,arg1,arg2))

	def clear_rules(self):
		self.rules = []
		self.sub_rules = []

