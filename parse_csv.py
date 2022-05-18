import pandas as pd
from statistics import median

from collections import defaultdict

def read_first_line(line, delete_prefix_on_config_name=True):
	line = line.split(",")

	configs = []
	last_config = None
	#skip the first empty line!
	for val in line[1:]:
		if val != "":
			if val == "min":
				break
			last_config = val.split("/")[-1]

		configs.append(last_config)

	return configs

def read_second_line(line):
	line = line.split(",")

	stats = []
	for stat in line[1:]:
		stats.append(stat)

	return stats

def setup_data_dict(config_names, stat_names):

	data = {}
	for config, stat in zip(config_names, stat_names):
		if config not in data:
			data[config] = {}

		data[config][stat] = []

	return data

def create_dataframes(data, instances, config_names, stat_names):

	dataframes = {}

	for stat in set(stat_names):
		temp_dict = {}
		for config in set(config_names):
			if stat in data[config]:
				temp_dict[config] = data[config][stat]

		dataframes[stat] = pd.DataFrame(temp_dict, index=instances)

	return dataframes

def create_single_dataframe(data, instances, config_names, stat_names):
	temp_dict = {}
	for stat in set(stat_names):
		for config in set(config_names):
			if stat in data[config]:
				temp_dict[f"{config}--{stat}"] = data[config][stat]

	df = pd.DataFrame(temp_dict, index=instances)

	return df

def merge_values_to_dict2(run_values, data, processsing_func):
	if run_values != {}:
		for config, stat_dict in run_values.items():
			for stat in stat_dict.keys():
				if run_values[config][stat] == []:
					#raise ValueError("Empty value for config {} and stat {}".format(config, stat))
					run_values[config][stat] = [None]
				val = processsing_func(run_values[config][stat], stat)
				data[config][stat].append(val)

	return data

def do_average(data, stat):
	if stat == "status":
		#special case for status!
		#if one of the values is 0, then give 0
		#if one of the values is 1, give 1
		#if one of the values is 3(optimum found) also give 1
		# else(unknown) give 0
		if 1 in data or 3 in data:
			val = 1
		else:
			val = 0
	else:
		val = sum(data) / len(data)

	return val

def do_median(data, stat):
	if stat == "status":
		#special case for status!
		#if one of the values is 0, then give 0
		#if one of the values is 1, give 1
		#if one of the values is 3(optimum found) also give 1
		# else(unknown) give 0
		if 1 in data or 3 in data:
			val = 1
		else:
			val = 0
	else:
		val = median(data)

	return val

def do_first(data, stat):
	try:
		val = data[0]
	except IndexError:
		print(data)
		print(stat)
		raise

	return val

def do_nothing(data, stat):
	return data

processsing = {}
processsing["none"] = do_nothing
processsing["average"] = do_average
processsing["median"] = do_median
processsing["first"] = do_first

def read_csv(file_name, do_processing="average", delete_prefix_on_config_name=True, print_warn=False):
	# processsing can be: average, median, first, none
	# for now it will always treat the data as float!!
	# will throw error if its not possible to convert

	processing_func = processsing[do_processing]

	with open(file_name, "r") as f:
		config_names = read_first_line(f.readline(), delete_prefix_on_config_name) # read first line to get configs
		stat_names = read_second_line(f.readline()) # second line contains

		stat_names = stat_names[:len(config_names)]

		data = setup_data_dict(config_names, stat_names)
		instances = []
		run_values = defaultdict(lambda: defaultdict(list))

		for line in f.readlines():
			line = line.split(",")

			if line[0] == "" and line[1] == "":
				data = merge_values_to_dict2(run_values, data, processing_func)
				break

			if line[0] != "":
				# if line is not empty, then add the run_values to the dict!
				# only do this is run_values is not empty(should only be empty on the first pass)
				data = merge_values_to_dict2(run_values, data, processing_func)
				# reset run_values
				run_values = defaultdict(lambda: defaultdict(list))
				# from here on, we start with the next instance

				instances.append(line[0].strip())

			# after setting up the run_values dict we continue with parsing the linen
			line = line[1:]

			# first position is instance name so we start with second position
			for line_position in range(0, len(config_names)):
				config = config_names[line_position]
				stat = stat_names[line_position]

				try:
					run_values[config][stat].append(float(line[line_position]))
				except ValueError:
					if print_warn:
						print("WARNING: configuration {} on stat {} has a non float value {} on instance {}!".format(config, stat, line[line_position], instances[-1]))

		dataframes = create_dataframes(data, instances, config_names, stat_names)
		df = create_single_dataframe(data, instances, config_names, stat_names)
	
	return dataframes, df, config_names, stat_names

#file_name = "results-generalization-inc-4h-max-calls.csv"
#dataframes = read_csv(file_name, do_average=True)
