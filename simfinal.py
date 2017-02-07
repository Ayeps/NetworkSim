# This is a simpy based  simulation of a M/M/1 queue system

from decimal import *
getcontext().prec = 10
import random
import simpy
import math

RANDOM_SEED = 32 #old one was 33
SIM_TIME = 10000
MU = 1
buffer_size = 10
dropped_pkts = Decimal(0)
drop_rate = Decimal(0)
nodes_ready = 0
success = 0
collisions = 0


# make the class a function
# make the expo backoff function the class 


""" Queue system  """		
class server_queue:
	def __init__(self, env, arrival_rate, Packet_Delay, Server_Idle_Periods,name):
		self.server = simpy.Resource(env, capacity = 1)
		self.env = env
		self.queue_len = 0
		self.flag_processing = 0
		self.packet_number = 0
		self.sum_time_length = 0
		self.start_idle_time = 0
		self.arrival_rate = arrival_rate
		self.Packet_Delay = Packet_Delay
		self.Server_Idle_Periods = Server_Idle_Periods
		self.slotted_service_proc = env.process(self.slotted_service(env))
		self.ready = 0
		self.n = 0
		self.delay = 0
		self.name = name
		self.send_now = 0 
		self.flag = 0
		#self.packet_count = 0


		self.slot_ends = env.event()

	def process_packet(self, env, packet):						# dont make packet ready until correct time slot
		global nodes_ready
		global success
		with self.server.request() as req:#-------remove?
			start = env.now
			yield req														# yield till available to be processed

			self.send_now = 0 
			
			print("============================================")
			print(" packet available at-->",(env.now,self.name))

			print(" waiting for slot")
			self.ready = 1
			print("self.send_now",(self.send_now))
			
			
			while self.send_now == 0 :	
				
				if self.delay == 0:				# attempt to send, node is ready 
					nodes_ready += 1
					self.flag = 1
					print('flag set',(self.name))
					
				yield self.slot_ends											#yield until slot ends
				
				if self.flag == 1:				# if you attempted, regardless if send or not
					print('flag reset',(self.name))
					self.flag = 0 
					nodes_ready -= 1
				
			
			self.send_now == 0 
			success += 1

			yield env.timeout(random.expovariate(MU))			# process ended ready to send
			latency = env.now - packet.arrival_time
			self.Packet_Delay.addNumber(latency)
			#print("Packet number {0} with arrival time {1} latency {2}".format(packet.identifier, packet.arrival_time, latency))


			self.queue_len -= 1
			if self.queue_len == 0:
				self.flag_processing = 0
				self.start_idle_time = env.now

			#---------------------------------------send packet so reset all variables





	def packets_arrival(self, env):
		# packet arrivals
                global dropped_pkts # need this else get the local variable unbound error	
	        global drop_rate # need this else get the local variable unbound error
		while True:
		     # Infinite loop for generating packets
			yield env.timeout(random.expovariate(self.arrival_rate))
			  # arrival time of one packet

			self.packet_number += 1
			  # packet id
			arrival_time = env.now
			#print(self.num_pkt_total, "packet arrival")
			new_packet = Packet(self.packet_number,arrival_time)
			if self.flag_processing == 0:
				self.flag_processing = 1
				idle_period = env.now - self.start_idle_time
				self.Server_Idle_Periods.addNumber(idle_period)
				#print("Idle period of length {0} ended".format(idle_period))
			if self.queue_len < buffer_size: #if buffer still has space
				self.queue_len += 1
				env.process(self.process_packet(env, new_packet))   #-------remove?
			else: #buffer_size is greater than queue length
				dropped_pkts += 1


	def slotted_service(self,env):			# use manual release, and release resourse here
		global SIM_TIME							# check how this works too!
		global success
		global nodes_ready
		global collisions

		#env.process(self.packets_arrival(env))  # if conflict, yield till calculated time slot, check
		for x in range(1,10000):
			yield env.timeout(1)

			print('       ')
			print('       ')			
			print('Timeout!---------------------------------------------------------> ',(self.name,env.now))

			print(' During current timeout ------------------')
			print(' delay -> ',(self.delay))
			print(' self.ready =  ',(self.ready ))
			print(' nodes_ready----- ',(nodes_ready))
			
			if self.ready == 1:										# if ready 
	
				if self.delay == 0:									# and if no delay 

					#nodes_ready += 1
					#print(' nodes_ready----- ',(nodes_ready))	
					if nodes_ready == 1:     						# and only one node wants to transmit 
						print(" processing packet recieved during previous slot")
						
						#nodes_ready -= 1							#------add number of successses
						self.send_now = 1
						self.n = 0
						self.ready = 0								#sending packet, so reset all variables 
						self.delay = 0
						#self.slot_ends.succeed()					# only one node needs to send, and send packet
						#self.slot_ends = self.env.event()


					elif nodes_ready > 1:		# and if more than one node wants to transmit 
						collisions += 1
						self.n += 1
						K = min(self.n,10)
						self.delay = random.randint(0,pow(2,K))
						print(' Too many nodes, try again ')
						print('Delay',self.delay)
						
						print('**********************************************************************************')
						print('**********************************************************************************')
						#nodes_ready -= 1
				else:				# if there is delay 
					self.delay -= 1
					#print(' nodes_ready----- ',(nodes_ready))		
					
					
				self.slot_ends.succeed()					
				self.slot_ends = self.env.event()
			
					

""" Packet class """			
class Packet:
	def __init__(self, identifier, arrival_time):
		self.identifier = identifier
		self.arrival_time = arrival_time


class StatObject:
    def __init__(self):
        self.dataset =[]

    def addNumber(self,x):
        self.dataset.append(x)
    def sum(self):
        n = len(self.dataset)
        sum = 0
        for i in self.dataset:
            sum = sum + i
        return sum
    def mean(self):
        n = len(self.dataset)
        sum = 0
        for i in self.dataset:
            sum = sum + i
        return sum/n
    def maximum(self):
        return max(self.dataset)
    def minimum(self):
        return min(self.dataset)
    def count(self):
        return len(self.dataset)
    def median(self):
        self.dataset.sort()
        n = len(self.dataset)
        if n//2 != 0: # get the middle number
            return self.dataset[n//2]
        else: # find the average of the middle two numbers
            return ((self.dataset[n//2] + self.dataset[n//2 + 1])/2)
    def standarddeviation(self):
        temp = self.mean()
        sum = 0
        for i in self.dataset:
            sum = sum + (i - temp)**2
        sum = sum/(len(self.dataset) - 1)
        return math.sqrt(sum)




def main():
	print("Simple queue system model:mu = {0}".format(MU))
	print ("{0:<9} {1:<9} {2:<9} {3:<9} {4:<9} {5:<9} {6:<9} {7:<9}".format(
        "Lambda", "Count", "Min", "Max", "Mean", "Median", "Sd", "Utilization"))
	random.seed(RANDOM_SEED)
	for arrival_rate in [0.01]:

		env = simpy.Environment()
		Packet_Delay = StatObject()
		Server_Idle_Periods = StatObject()

		router1 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(1))
		router2 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(2))
		router3 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(3))
		router4 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(4))
		router5 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(5))
		router6 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(6))
		router7 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(7))
		router8 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(8))
		router9 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(9))
		router10 = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(10))		
		
		
		
		
		env.process(router1.packets_arrival(env))
		env.process(router2.packets_arrival(env))
		env.process(router3.packets_arrival(env))
		env.process(router4.packets_arrival(env))
		env.process(router5.packets_arrival(env))	
		env.process(router6.packets_arrival(env))
		env.process(router7.packets_arrival(env))
		env.process(router8.packets_arrival(env))
		env.process(router9.packets_arrival(env))
		env.process(router10.packets_arrival(env))	

		
		env.run(until=SIM_TIME)


		print('number of successes out of 10,000',success)

		print('number of collisions out of 10,000',collisions)
		# router = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods,'Queue'+str(1))
		# env.process(router.packets_arrival(env))		

		#env.run(until=SIM_TIME)
		
		# router = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods)
		# env.process(router.packets_arrival(env))
		# env.run(until=SIM_TIME)

if __name__ == '__main__': main()

#================================================================
#================================================================






