import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth
import seaborn as sns
import matplotlib.pyplot as plt

# /Users/freyenterprise/documents/work/projects/metromile/131006779\ all_driving_data/sadie
def find_month(month, year):
	'''
	INPUT:
		month: int
			format: M or MM for 1- or 2- digit month
		year: int
			format: YYYY
	OUTPUT:
		best match filename in available data
	'''
	files = os.listdir('.')
	year = datetime.now().year if not year else year
	month = datetime.now().month if month == None else month
	filename = str(year) + '-' + str(month).zfill(2) + '.csv'
	if filename not in files:
		print 'File not found. Finding another...'
		filename = filter(lambda fn: fn.endswith('.csv'), files)[-1]
	return filename

def load_month_data(filename):
	'''
	returns a dataframe of sampled driving data subset to the variables of interest
	INPUT:
		filename: str
			format: YYYY-MM.csv
	OUTPUT:
		pandas DataFrame
	'''
	original_df  = pd.read_csv(filename, parse_dates=['recordDateTime'])
	cols_ofi = ['recordDateTime', 
		'latitude', 
		'longitude', 
		'vehicleSpeedSensorKmPerHour', 
		'rpm'
		]
	return original_df[cols_ofi]

def clean_original(original_df):
	'''
	returns a dataframe of filtered driving data samples where the car is moving and on
	INPUT:
		pandas DataFrame
	OUTPUT:
		pandas DataFrame
			index = original_df.index
	'''
	df = original_df.dropna(axis = 0, how = 'any')
	is_moving = df['vehicleSpeedSensorKmPerHour'] > 0.
	is_on = df['rpm'] > 0.
	mask = is_moving & is_on
	return df[mask]

def visualize_df(df, time_period, title, savefig = True):
	'''
	create a prelimiary scatter of car vs. engine speed

	'''
	df.plot(x = 'rpm', y = 'vehicleSpeedSensorKmPerHour', kind = 'scatter', alpha = .2)
	plt.suptitle('CAR SPEED vs. ENGINE SPEED')
	plt.title(' '.join([title, time_period]))
	if savefig:
		plt.savefig('images/' + time_period.replace('-', '') + '_' + title.replace(' ','') + '.png')
	plt.show()
	return

def mean_shift_cluster(df, feature):
	'''
	return a clustered MeanShift object fit to univariate feature of a DataFrame
	INPUT:
		df: pandas DataFrame
		feature: str
	OUTPUT:
		ms: MeanShift object fit to X
	'''
	x = df[feature]
	X = np.array(zip(x,np.zeros(len(x))), dtype=np.float)
	bandwidth = estimate_bandwidth(X, quantile=0.1)
	ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
	ms.fit(X)
	return ms

def filter_neutral(df, ms):
	'''
	filters out all suspected datapoints where the drivetrain is in neutral based on rpm

	INPUT:
		pandas DataFrame (clean and complete)
	OUTPUT:
		pandas DataFrame	
			index = original_df.index
	'''

	cluster_centers = ms.cluster_centers_[:,0]
	neutral_label = np.where(cluster_centers == cluster_centers.min())[0][0]
	ms_labels = ms.labels_
	neutral_mask = ms_labels == neutral_label
	return df[~neutral_mask]	

def make_polar_df(df):
	'''
	returns a dataframe of the data in polar coordinates (rho and phi) indexed to the original
	INPUT:
		pandas DataFrame (clean and complete)
	OUTPUT:
		pandas DataFrame
			index: original_df.index
			columns: 'rho', 'phi', float
	'''
	x = df['rpm']
	y = df['vehicleSpeedSensorKmPerHour']
	rho = np.sqrt(x ** 2 + y ** 2)
	phi = np.arctan2(y, x)
	return pd.DataFrame({'rho' : rho, 'phi' : phi})

def visualize_polar_df(polar_df, time_period, title, lines = np.array([]), savefig = True):
	polar_df.plot(x = 'rho', y = 'phi', kind = 'scatter', alpha = .2)
	plt.suptitle('PHI (vehicle/engine speed ratio) vs. RHO (magnitude)')
	plt.title(' '.join([title, time_period]))
	if lines.any():
		for y in lines:
			plt.axhline(y)
	if savefig:
		plt.savefig('images/' + time_period.replace('-', '') + '_' + title.replace(' ','') + '.png')
	plt.show()
	return

def label_gears(polar_df, phi_ms, n_gears):	
	'''
	return labeled dataframe of likely gears plus the values of theta 
	'''
	# n_gears = 5
	ms_cluster_centers = phi_ms.cluster_centers_[:,0]
	ms_label_dict = dict(enumerate(ms_cluster_centers))
	ms_label_dict = {v:k for k,v in ms_label_dict.iteritems()}
	ms_labels = phi_ms.labels_
	label_counts = np.bincount(ms_labels)
	thresh = sorted(label_counts, reverse = True)[n_gears - 1]
	wanted_labels = np.where(label_counts >= thresh)[0]
	rev_ms_label_dict = {v:k for k,v in ms_label_dict.iteritems()}
	gear_dict = dict(enumerate(sorted([rev_ms_label_dict[ms_label] for ms_label in wanted_labels]),1))

	gear_dict = {v:k for k,v in gear_dict.iteritems()}
	gear_lines = np.array(gear_dict.keys())
	translate_dict = {}
	for k,v in ms_label_dict.iteritems():
		ms_label = v
		if gear_dict.has_key(k):
			gear_label = gear_dict[k]
		else:
			gear_label = 0
		translate_dict[ms_label] = gear_label
	polar_df['ms_label'] = ms_labels
	polar_df['gear'] = polar_df['ms_label'].replace(translate_dict)
	return polar_df.drop('ms_label', axis = 1), np.sort(gear_dict.keys())

def visualize_gears(merged, time_period, savefig = True):
	sns.lmplot(x = 'rpm', 
		y = 'vehicleSpeedSensorKmPerHour', 
		data = merged, 
		hue = 'gear',
		fit_reg = False,
		# legend = False,
		scatter_kws = {'marker' : 'D',
						'alpha' : 0.4, 
						's' : 30
						})
	# plt.legend(title = 'Gear', bbox_to_anchor = (1.13, 1.))
	plt.title('CAR SPEED vs. ENGINE SPEED (by gears) : ' + time_period)
	if savefig:
		plt.savefig('images/' + time_period.replace('-', '') + '_' + 'clusteredgears.png')
	plt.show()
	return

def phi_to_revpermeter(phi):
	'''
	return a scalar of revolutions/meter given phi
	'''
	nom_rpm = 1 * np.cos(phi)
	nom_kmph = 1 * np.sin(phi)
	mpm = nom_kmph * 1000. / 60.
	return nom_rpm/mpm

def main(return_vals = False, write_data = False, savefig = False):
	''' run from working directory of data'''

	month = raw_input('Enter month number : [1, 2, ..., 12] : ') 
	year = raw_input('Enter year (e.g. 2016) : ')
	filename = find_month(month, year)
	time_period = filename.split('.')[0] 
	original_df = load_month_data(filename)
	visualize_df(original_df, time_period, 'original data', savefig = savefig)

	df = clean_original(original_df)
	visualize_df(df, time_period, 'on and moving', savefig = savefig)
	rpm_ms = mean_shift_cluster(df, 'rpm')
	df = filter_neutral(df, rpm_ms)
	visualize_df(df, time_period, 'non neutral rpm', savefig = savefig)
	polar_df = make_polar_df(df)
	visualize_polar_df(polar_df, time_period, 'unclustered polar', savefig = savefig)
	
	phi_ms = mean_shift_cluster(polar_df, 'phi')
	n_gears = int(raw_input('Enter number of (non-reverse) gears : '))
	polar_df, lines = label_gears(polar_df, phi_ms, n_gears)
	visualize_polar_df(polar_df, time_period, 'clustered polar', lines, savefig = savefig)

	merged = df.merge(polar_df, how = 'right', left_index = True, right_index = True)
	visualize_gears(merged, time_period)
	revpermeter = np.array([phi_to_revpermeter(phi) for phi in lines])
	tire_d = float(raw_input('Enter the tire diameter in inches : '))
	print
	# tire_d = 26.5 # my tire d in inches
	tire_c = np.pi * tire_d * .0254 # in meters
	revperroll = revpermeter * tire_c
	axle_ratio = raw_input('If known, enter the axle ratio. If not, hit [return] : ')
	print 
	if axle_ratio:
		axle_ratio = float(axle_ratio)
	else:
		axle_ratio = revperroll[3] # fourth gear is often 1:1
	gear_ratios = revperroll/axle_ratio
	print 'Best guesses for Gear Ratios:'
	for g, r in enumerate(gear_ratios, 1):
		print 'Gear %d : %.2f' % (g, r)
	original_df.to_csv('pydata/' + time_period.replace('-', '') + '_' + 'originaldf.csv')
	merged.to_csv('pydata/' + time_period.replace('-', '') + '_' + 'merged.csv')	
	if return_vals:
		return original_df, polar_df, merged, gear_ratios

if __name__ == '__main__':
	main()