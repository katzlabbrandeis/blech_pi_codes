# Import stuff
import time
import RPi.GPIO as GPIO
from subprocess import Popen
import easygui
import numpy as np
import os
import random
import ast

# The BOARD mode allows referring to the GPIO pins by their number on the board
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Clear all outputs from Pi
def clearall():
	outports = [16, 18, 21, 22, 23, 24]
	inports = [40, 37, 35, 33, 32, 31]
	pokelights = [8, 15]
	houselight = 10

	lasers = [38, 11]

	for i in outports:
		GPIO.setup(i, GPIO.OUT)
		GPIO.output(i, 0)
	for i in inports:
		GPIO.setup(i, GPIO.IN, GPIO.PUD_UP)
	for i in pokelights:
		GPIO.setup(i, GPIO.OUT)
		GPIO.output(i, 0)
	for i in lasers:
		GPIO.setup(i, GPIO.OUT)
		GPIO.output(i, 0)
	GPIO.setup(houselight, GPIO.OUT)
	GPIO.output(houselight, 0)

# Clear tastant lines
def clearout(outports = [16, 18, 21, 22, 23, 24], dur = 5):

	GPIO.setmode(GPIO.BOARD)
	for i in outports:
		GPIO.setup(i, GPIO.OUT)

	for i in outports:
		GPIO.output(i, 1)
	time.sleep(dur)
	for i in outports:
		GPIO.output(i, 0)

	print('Tastant line clearing complete.')

# Calibrate tastant lines
def calibrate(outports = [16, 18, 21, 22, 23, 24], opentime = 0.015, repeats = 5):

	GPIO.setmode(GPIO.BOARD)
	for i in outports:
		GPIO.setup(i, GPIO.OUT)

	for rep in range(repeats):
		for i in outports:
			GPIO.output(i, 1)
		time.sleep(opentime)
		for i in outports:
			GPIO.output(i, 0)
		time.sleep(2)

	print('Calibration procedure complete.')

# Passive H2O deliveries
def passive(outport = 16, opentime = 0.015, iti = 15, trials = 100):

	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(outport, GPIO.OUT)

	time.sleep(10)
	
	for trial in range(trials):
		GPIO.output(outport, 1)
		time.sleep(opentime)
		GPIO.output(outport, 0)
		print('Trial '+str(trial+1)+' of '+str(trials)+' completed.')
		time.sleep(iti)

	print('Passive deliveries completed')

# Passive deliveries with video recordings and laser inactivation
def passive_with_video_and_lasers(outports = [16, 18, 21, 22, 23, 24], intan_inports = [40, 37, 35, 33, 32, 31], tastes = ['NaCl', 'Sucrose', 'citriacid', 'quinine', 'a', 'b'], opentimes = [0.1, 0.1, 0.010, 0.010, 0.010, 0.010], iti = 20, repeats = 30):

	# Get the number of different inactivation windows to be used from the user and convert to integer
	num_windows = easygui.multenterbox(msg = 'How many different inactivation windows do you want to use? (greater than 0 - do not use laser code if you do not want to inactivate)', fields = ['# of different inactivation windows in the experiment'])
	num_windows = int(num_windows[0])

	# Set the outports to outputs
	GPIO.setmode(GPIO.BOARD)
	for i in outports:
		GPIO.setup(i, GPIO.OUT)
		GPIO.output(i, 0)

	# Set the input lines for Intan to outputs
	for i in intan_inports:
		GPIO.setup(i, GPIO.OUT)
		GPIO.output(i, 0)

	# Turn on green house light
	houselight = 10
	GPIO.setup(houselight, GPIO.OUT)
	GPIO.output(houselight, 1)
	
	# Define the port for the video cue light, and set it as output
	video_cue = 8
	GPIO.setup(video_cue, GPIO.OUT)
	GPIO.output(video_cue, 0)

	# Define the laser ports and set them as outputs
	lasers = [11, 38] # [11, 38]
	for laser in lasers:
		GPIO.setup(laser, GPIO.OUT)
		GPIO.output(laser, 0)

	# Define the laser inputs to Intan and set them as outputs
	intan_lasers = [13, 36] #[10, 36] # going to digin 7
	for laser in intan_lasers:
		GPIO.setup(laser, GPIO.OUT)
		GPIO.output(laser, 0)

	# Make an ordered array of the number of tastes (length of outports)
	taste_array = []
	laser_array = []
	for i in range(len(outports)*repeats):
		taste_array.append(int(i%len(outports)))
		laser_array.append(int((i/len(outports))%(num_windows + 1)))

	# Randomize the array of tastes and lasers together, and print them
	combined = list(zip(taste_array, laser_array))
	random.shuffle(combined)
	taste_array, laser_array = zip(*combined)
	print("Chosen sequence of tastes:" + '\n' + str(taste_array))
	print("Chosen sequence of laser trials" + '\n' + str(laser_array))

	# Ask the user for the directory to save the video files in	
	directory = easygui.diropenbox(msg = 'Select the directory to save the videos from this experiment', title = 'Select directory')
	# Change to that directory
	os.chdir(directory)

	# Ask the user for the durations of the laser stimulus in the different inactivation windows/protocols
	inactivation_times = []
	for i in range(num_windows):
		times = easygui.multenterbox(msg = 'Timing of the lasers (secs, -ive is pre taste delivery) in window %i' % (i+1), fields = ['Laser on time (cannot be less than -1.0 secs)', 'Laser off time (cannot be more than 5.0 secs)'])
		for j in range(len(times)):
			times[j] = float(times[j])
		inactivation_times.append(times)
	
	# A 10 sec wait before things start
	time.sleep(10)

	# Deliver the tastes according to the order in taste_array
	trials = [1 for i in range(len(outports))] # Counter of taste trials completed
	for i in range(len(taste_array)):
		# Make filename, and start the video in a separate process
		process = Popen('sudo streamer -q -c /dev/video0 -s 1280x720 -f jpeg -t 240 -r 30 -j 75 -w 0 -o ' + tastes[taste_array[i]] + '_trial_' + str(trials[taste_array[i]]) + '.avi', shell = True, stdout = None, stdin = None, stderr = None, close_fds = True)
		
		# Pick inactivation times according to the time window to be used in this trial - will give error if this was an uninactivated trial, hence put it in a try loop
		try:
			laser_times = inactivation_times[laser_array[i]]
		except:
			laser_times = [0.0, 0.0]

		# Wait for 2 sec total, before delivering tastes
		# Condition 1 for lasers when the start time is less than 0
		if laser_array[i] < num_windows and laser_times[0] < 0.0:		
			time.sleep(2.0 - (laser_times[0]*(-1) - opentimes[taste_array[i]]))
			for laser in lasers:
				GPIO.output(laser, 1)
			for laser in intan_lasers:
				GPIO.output(laser, 1)
			time.sleep(laser_times[0]*(-1) - opentimes[taste_array[i]])
		else: 
			time.sleep(2.0)

		# Switch on the cue light
		GPIO.output(video_cue, 1)

		# Deliver the taste, and send outputs to Intan
		GPIO.output(outports[taste_array[i]], 1)
		GPIO.output(intan_inports[taste_array[i]], 1)
		time.sleep(opentimes[taste_array[i]])	
		GPIO.output(outports[taste_array[i]], 0)
		GPIO.output(intan_inports[taste_array[i]], 0)

		# Condition 2 for lasers when the start time is >= 0 and <= 0.05
		if laser_array[i] < num_windows and laser_times[0] >= 0 and laser_times[0] <= 0.05:
			time.sleep(laser_times[0])			
			for laser in lasers:
				GPIO.output(laser, 1)
			for laser in intan_lasers:
				GPIO.output(laser, 1)
		
		# Switch the light off after 50 ms total
		if laser_times[0] >= 0 and laser_times[0] <= 0.05:
			time.sleep(0.050 - laser_times[0])
		else:
			time.sleep(0.050)
		GPIO.output(video_cue, 0)

		# Sleep till laser switch on time, if its post taste delivery, and switch it on
		# Sleep till laser switch off time, and switch it off
		if laser_array[i] < num_windows:
			if laser_times[0] >= 0.05: # Condition 3 for lasers when the start time is greater than 0.05
				time.sleep(laser_times[0] - 0.050)
				for laser in lasers:
					GPIO.output(laser, 1)
				for laser in intan_lasers:
					GPIO.output(laser, 1)
				time.sleep(laser_times[1] - laser_times[0])
				for laser in lasers:
					GPIO.output(laser, 0)
				for laser in intan_lasers:
					GPIO.output(laser, 0)
			else:
				time.sleep(laser_times[1] - 0.050)
				for laser in lasers:
					GPIO.output(laser, 0)
				for laser in intan_lasers:
					GPIO.output(laser, 0)
		
		# Increment the trial counter for the taste by 1
		trials[taste_array[i]] += 1

		# Print number of trials completed
		print("Trial " + str(np.sum(trials) - len(outports)) + " of " + str(len(taste_array)) + " completed.")

		# Wait for the iti before delivering next taste
		time.sleep(iti)
		
	GPIO.output(houselight, 0)

def passive_cue(
    outports=[16, 18, 21, 23, 24], 
    intaninputs=[40, 37, 33, 32, 31], 
    opentimes=[0.01], itimin=10, itimax=30, trials=150,
    cue_input = 22):

    # Setup pi board GPIO ports
    GPIO.setmode(GPIO.BOARD)
    for i in outports:
        GPIO.setup(i, GPIO.OUT)
    for i in intaninputs:
        GPIO.setup(i, GPIO.OUT)
    GPIO.setup(cue_input, GPIO.OUT)

    # Set and radomize trial order
    tot_trials = len(outports) * trials
    count = 0
    #trial_array = trials * range(len(outports))
    trial_array = trials * list(np.arange(len(outports)))
    random.shuffle(trial_array)

    time.sleep(3)

    # Loop through trials
    for i in trial_array:
        GPIO.output(cue_input, 1)
        #time.sleep(1) #if you want cue on before taste delivery, uncomment
        #GPIO.output(cue_input, 0)
        #time.sleep(1)
        GPIO.output(outports[i], 1)
        GPIO.output(intaninputs[i], 1)
        time.sleep(opentimes[i])

        GPIO.output(outports[i], 0)
        GPIO.output(intaninputs[i], 0)
        time.sleep(1)
        GPIO.output(cue_input, 0)
        count += 1
        iti = random.randint(itimin, itimax)
        print('Trial '+str(count)+' of '+str(tot_trials) +
              ' completed. ITI = '+str(iti)+' sec.')
        time.sleep(iti)

    print('Passive deliveries completed')

# Passive deliveries with video recordings


# Passive deliveries with video commented out and laser inactivation ******KM/EC
def passive_with_lasers(outports = [16, 18, 21, 22, 23, 24], intan_inports = [40, 37, 35, 33, 32, 31], tastes = ['NaCl', 'Sucrose', 'citriacid', 'quinine'], opentimes = [0.010, 0.010, 0.010, 0.010], iti = 20, repeats = 30):

	# Get the number of different inactivation windows to be used from the user and convert to integer
	num_windows = easygui.multenterbox(msg = 'How many different inactivation windows do you want to use? (greater than 0 - do not use laser code if you do not want to inactivate)', fields = ['# of different inactivation windows in the experiment'])
	num_windows = int(num_windows[0])

	# Set the outports to outputs
	GPIO.setmode(GPIO.BOARD)
	for i in outports:
		GPIO.setup(i, GPIO.OUT)
		GPIO.output(i, 0)

	# Set the input lines for Intan to outputs
	for i in intan_inports:
		GPIO.setup(i, GPIO.OUT)
		GPIO.output(i, 0)


	# Define the laser ports and set them as outputs
	lasers = [38]
	for laser in lasers:
		GPIO.setup(laser, GPIO.OUT)
		GPIO.output(laser, 0)

	# Define the laser inputs to Intan and set them as outputs
	intan_lasers = [36]
	for laser in intan_lasers:
		GPIO.setup(laser, GPIO.OUT)
		GPIO.output(laser, 0)

	# Make an ordered array of the number of tastes (length of outports)
	taste_array = []
	laser_array = []
	for i in range(len(outports)*repeats):
		taste_array.append(int(i%len(outports)))
		laser_array.append(int((i/len(outports))%(num_windows + 1)))

	# Randomize the array of tastes and lasers together, and print them
	combined = list(zip(taste_array, laser_array))
	random.shuffle(combined)
	taste_array, laser_array = zip(*combined)
	print("Chosen sequence of tastes:" + '\n' + str(taste_array))
	print("Chosen sequence of laser trials" + '\n' + str(laser_array))

	# Ask the user for the directory to save the video files in	
	#directory = easygui.diropenbox(msg = 'Select the directory to save the videos from this experiment', title = 'Select directory')
	# Change to that directory
	#os.chdir(directory)

	# Ask the user for the durations of the laser stimulus in the different inactivation windows/protocols
	inactivation_times = []
	for i in range(num_windows):
		times = easygui.multenterbox(msg = 'Timing of the lasers (secs, -ive is pre taste delivery) in window %i' % (i+1), fields = ['Laser on time (cannot be less than -1.0 secs)', 'Laser off time (cannot be more than 5.0 secs)'])
		for j in range(len(times)):
			times[j] = float(times[j])
		inactivation_times.append(times)
	
	# Turn on cue light for 1 sec 
    # Then, a 5 min wait before things start
	time.sleep(10)
	cue_input = 8
	cue_intan = 15
	GPIO.setup(cue_input, GPIO.OUT)
	GPIO.setup(cue_intan, GPIO.OUT)
	GPIO.output(cue_input, 1)
	GPIO.output(cue_intan, 1)
	time.sleep(1)
	GPIO.output(cue_input, 0)
	GPIO.output(cue_intan, 0)
	time.sleep(10)

	# Deliver the tastes according to the order in taste_array
	trials = [1 for i in range(len(outports))] # Counter of taste trials completed
	for i in range(len(taste_array)):
		# Make filename, and start the video in a separate process
		#process = Popen('sudo streamer -q -c /dev/video0 -s 1280x720 -f jpeg -t 240 -r 30 -j 75 -w 0 -o ' + tastes[taste_array[i]] + '_trial_' + str(trials[taste_array[i]]) + '.avi', shell = True, stdout = None, stdin = None, stderr = None, close_fds = True)
		
		# Pick inactivation times according to the time window to be used in this trial - will give error if this was an uninactivated trial, hence put it in a try loop
		try:
			laser_times = inactivation_times[laser_array[i]]
		except:
			laser_times = [0.0, 0.0]

		# Wait for 2 sec total, before delivering tastes
		# Condition 1 for lasers when the start time is less than 0
		if laser_array[i] < num_windows and laser_times[0] < 0.0:		
			time.sleep(2.0 - (laser_times[0]*(-1) - opentimes[taste_array[i]]))
			for laser in lasers:
				GPIO.output(laser, 1)
			for laser in intan_lasers:
				GPIO.output(laser, 1)
			time.sleep(laser_times[0]*(-1) - opentimes[taste_array[i]])
		else: 
			time.sleep(2.0)


		# Deliver the taste, and send outputs to Intan
		GPIO.output(outports[taste_array[i]], 1)
		GPIO.output(intan_inports[taste_array[i]], 1)
		time.sleep(opentimes[taste_array[i]])	
		GPIO.output(outports[taste_array[i]], 0)
		GPIO.output(intan_inports[taste_array[i]], 0)

		# Condition 2 for lasers when the start time is >= 0 and <= 0.05
		if laser_array[i] < num_windows and laser_times[0] >= 0 and laser_times[0] <= 0.05:
			time.sleep(laser_times[0])			
			for laser in lasers:
				GPIO.output(laser, 1)
			for laser in intan_lasers:
				GPIO.output(laser, 1)
		
		# Switch the light off after 50 ms total
		if laser_times[0] >= 0 and laser_times[0] <= 0.05:
			time.sleep(0.050 - laser_times[0])
		else:
			time.sleep(0.050)

		# Sleep till laser switch on time, if its post taste delivery, and switch it on
		# Sleep till laser switch off time, and switch it off
		if laser_array[i] < num_windows:
			if laser_times[0] >= 0.05: # Condition 3 for lasers when the start time is greater than 0.05
				time.sleep(laser_times[0] - 0.050)
				for laser in lasers:
					GPIO.output(laser, 1)
				for laser in intan_lasers:
					GPIO.output(laser, 1)
				time.sleep(laser_times[1] - laser_times[0])
				for laser in lasers:
					GPIO.output(laser, 0)
				for laser in intan_lasers:
					GPIO.output(laser, 0)
			else:
				time.sleep(laser_times[1] - 0.050)
				for laser in lasers:
					GPIO.output(laser, 0)
				for laser in intan_lasers:
					GPIO.output(laser, 0)
		
		# Increment the trial counter for the taste by 1
		trials[taste_array[i]] += 1

		# Print number of trials completed
		print("Trial " + str(np.sum(trials) - len(outports)) + " of " + str(len(taste_array)) + " completed.")

		# Wait for the iti before delivering next taste
		time.sleep(iti)
		


# Passive deliveries with video and lasers can be fired singly
# Fires lasers in 4 conditions: Laser 1 alone, Laser 2 alone, both lasers or none
def passive_with_video_and_lasers_single(outports = [16, 18, 21, 22, 23, 24], intan_inports = [40, 37, 35, 33, 32, 31], tastes = ['water', 'saccharin', 'salt', 'concqui'], opentimes = [0.010, 0.010, 0.010, 0.010], iti = 15, repeats = 30):
	# Set the outports to outputs
	GPIO.setmode(GPIO.BOARD)
	for i in outports:
		GPIO.setup(i, GPIO.OUT)
		GPIO.output(i, 0)

	# Set the input lines for Intan to outputs
	for i in intan_inports:
		GPIO.setup(i, GPIO.OUT)
		GPIO.output(i, 0)

	# Turn on green house light
	houselight = 8
	GPIO.setup(houselight, GPIO.OUT)
	GPIO.output(houselight, 1)
	
	# Define the port for the video cue light, and set it as output
	video_cue = 10
	GPIO.setup(video_cue, GPIO.OUT)
	GPIO.output(video_cue, 0)

	# Define the laser ports and set them as outputs
	lasers = np.array([11, 38])
	for laser in lasers:
		GPIO.setup(laser, GPIO.OUT)
		GPIO.output(laser, 0)

	# Define the laser inputs to Intan and set them as outputs
	intan_lasers = np.array([10, 36])
	for laser in intan_lasers:
		GPIO.setup(laser, GPIO.OUT)
		GPIO.output(laser, 0)

	# Define the different laser conditions
	on_lasers = [[], [0], [1], [0, 1]]

	# Make an ordered array of the number of tastes (length of outports)
	taste_array = []
	laser_array = []
	for i in range(len(outports)*repeats):
		taste_array.append(int(i%len(outports)))
		laser_array.append(int((i/len(outports))%(4)))	

	# Randomize the array of tastes and lasers together, and print them
	combined = zip(taste_array, laser_array)
	random.shuffle(combined)
	taste_array, laser_array = zip(*combined)
	print("Chosen sequence of tastes:" + '\n' + str(taste_array))
	print("Chosen sequence of laser trials" + '\n' + str(laser_array))

	# Ask the user for the directory to save the video files in	
	directory = easygui.diropenbox(msg = 'Select the directory to save the videos from this experiment', title = 'Select directory')
	# Change to that directory
	os.chdir(directory)

	# Ask the user for the durations of the laser stimulus in the different inactivation windows/protocols
	inactivation_times = easygui.multenterbox(msg = 'Timing of the lasers (secs, -ive is pre taste delivery) in window %i' % (i+1), fields = ['Laser on time (cannot be less than -1.0 secs)', 'Laser off time (cannot be more than 5.0 secs)'])
	for j in range(len(inactivation_times)):
		inactivation_times[j] = float(inactivation_times[j])
		
	# A 10 sec wait before things start
	time.sleep(10)

	# Deliver the tastes according to the order in taste_array
	trials = [1 for i in range(len(outports))] # Counter of taste trials completed
	for i in range(len(taste_array)):
		# Make filename, and start the video in a separate process
		process = Popen('sudo streamer -q -c /dev/video0 -s 1280x720 -f jpeg -t 240 -r 30 -j 75 -w 0 -o ' + tastes[taste_array[i]] + '_trial_' + str(trials[taste_array[i]]) + '.avi', shell = True, stdout = None, stdin = None, stderr = None, close_fds = True)
		
		# Pick inactivation times
		laser_times = inactivation_times

		# Pick the lasers to be switched on
		this_lasers = on_lasers[laser_array[i]]
		
		# Wait for 2 sec total, before delivering tastes
		# Condition 1 for lasers when the start time is less than 0
		if laser_array[i] > 0 and laser_times[0] < 0.0:		
			time.sleep(2.0 - (laser_times[0]*(-1) - opentimes[taste_array[i]]))
			for laser in lasers[this_lasers]:
				GPIO.output(laser, 1)
			for laser in intan_lasers[this_lasers]:
				GPIO.output(laser, 1)
			time.sleep(laser_times[0]*(-1) - opentimes[taste_array[i]])
		else: 
			time.sleep(2.0)

		# Switch on the cue light
		GPIO.output(video_cue, 1)

		# Deliver the taste, and send outputs to Intan
		GPIO.output(outports[taste_array[i]], 1)
		GPIO.output(intan_inports[taste_array[i]], 1)
		time.sleep(opentimes[taste_array[i]])	
		GPIO.output(outports[taste_array[i]], 0)
		GPIO.output(intan_inports[taste_array[i]], 0)

		# Condition 2 for lasers when the start time is >= 0 and <= 0.05
		if laser_array[i] > 0 and laser_times[0] >= 0 and laser_times[0] <= 0.05:
			time.sleep(laser_times[0])			
			for laser in lasers[this_lasers]:
				GPIO.output(laser, 1)
			for laser in intan_lasers[this_lasers]:
				GPIO.output(laser, 1)
		
		# Switch the light off after 50 ms total
		if laser_times[0] >= 0 and laser_times[0] <= 0.05:
			time.sleep(0.050 - laser_times[0])
		else:
			time.sleep(0.050)
		GPIO.output(video_cue, 0)

		# Sleep till laser switch on time, if its post taste delivery, and switch it on
		# Sleep till laser switch off time, and switch it off
		if laser_array[i] > 0:
			if laser_times[0] >= 0.05: # Condition 3 for lasers when the start time is greater than 0.05
				time.sleep(laser_times[0] - 0.050)
				for laser in lasers[this_lasers]:
					GPIO.output(laser, 1)
				for laser in intan_lasers[this_lasers]:
					GPIO.output(laser, 1)
				time.sleep(laser_times[1] - laser_times[0])
				for laser in lasers[this_lasers]:
					GPIO.output(laser, 0)
				for laser in intan_lasers[this_lasers]:
					GPIO.output(laser, 0)
			else:
				time.sleep(laser_times[1] - 0.050)
				for laser in lasers[this_lasers]:
					GPIO.output(laser, 0)
				for laser in intan_lasers[this_lasers]:
					GPIO.output(laser, 0)
		
		# Increment the trial counter for the taste by 1
		trials[taste_array[i]] += 1

		# Print number of trials completed
		print("Trial " + str(np.sum(trials) - len(outports)) + " of " + str(len(taste_array)) + " completed.")

		# Wait for the iti before delivering next taste
		time.sleep(iti)
		
	GPIO.output(houselight, 0)

