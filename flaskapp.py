#! /usr/bin/env python3

import argparse
import json
import urllib
import requests
import os.path
import jinja2
# from scipy import stats
import numpy as np
import pandas as pd
import datetime
from datetime import date, timedelta
from pandas import Series, DataFrame, Panel
# import matplotlib.pyplot as plt
# from matplotlib.offsetbox import AnchoredText

from bokeh.io import show
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, RangeTool, Range1d, LinearAxis
from bokeh.plotting import figure, output_file, save
from bokeh.resources import CDN
from bokeh.embed import file_html, components
# print (bokeh.__version__)


from flask import Flask, render_template
app = Flask(__name__)



# @app.route('/about/')
# def about():
#     return render_template('about.html')



def fixdatestrings(dt):
    if dt < 10:
        dtS = '0' + str(dt)
    else:
        dtS = str(dt)
    return (dtS)


def read_files(url):
    # with open(filename) as data_file:
    df=pd.read_csv(url, skiprows=6)
    df = df.drop([0, 1])
    # print(df.columns)
  
    df.Date_Time = pd.to_datetime(df.Date_Time)
    df[['pressure_set_1', 'air_temp_set_1',
       'relative_humidity_set_1', 'wind_speed_set_1', 'wind_direction_set_1',
       'wind_gust_set_1', 'precip_accum_set_1', 'precip_accum_24_hour_set_1',
       'dew_point_temperature_set_1d', 'altimeter_set_1d']] = df[['pressure_set_1', 'air_temp_set_1',
       'relative_humidity_set_1', 'wind_speed_set_1', 'wind_direction_set_1',
       'wind_gust_set_1', 'precip_accum_set_1', 'precip_accum_24_hour_set_1',
       'dew_point_temperature_set_1d', 'altimeter_set_1d']].astype(float)
    return df

def StationPlot(ID):

	now = datetime.datetime.now()

	end = str(now.year) + fixdatestrings(now.month) + fixdatestrings(now.day) + fixdatestrings(now.hour)
	startdate = date.today() - timedelta(30)
	start = str(startdate.year) + fixdatestrings(startdate.month) + fixdatestrings(startdate.day)
	# print(start)
	# print (end)
	# 201904240000

	var = 'vars=pressure,air_temp,dew_point_temperature,relative_humidity,wind_speed,wind_direction,wind_gust,precip_accum,precip_accum_24_hour'

	filename ='https://api.mesowest.net/v2/stations/timeseries?&stid='+ID+'&start='+start+'0000&end='+end+'00&token=demotoken&r&obtimezone=local&'+var+'&output=csv'
	dat_df = read_files(filename) #load json and turn into dataframe.

	dates = np.array(dat_df.Date_Time , dtype=np.datetime64)
	dat_df['dates'] = np.array(dat_df.Date_Time , dtype=np.datetime64)
	source = ColumnDataSource(data=dat_df)
	# source = ColumnDataSource(data=dict(date=dates, temp=dat_df.air_temp_set_1, dew = dat_df.dew_point_temperature_set_1d))
	# print(dat_df.head())
	p = figure(plot_height=300, plot_width=800,
	            title=ID,
	           x_axis_type="datetime", x_axis_location="above",
	           background_fill_color="#efefef", x_range=(dates[-200], dates[-1]))
	# tools="xpan", toolbar_location=None
	p.line('dates', 'air_temp_set_1', source=source, legend = 'Air Temp', line_color="tomato")
	p.line('dates', 'dew_point_temperature_set_1d', source=source, legend = 'Dew Point', line_color="indigo" )
	p.y_range = Range1d(
	    dat_df.dew_point_temperature_set_1d.min() , dat_df.air_temp_set_1.max() +2)

	p.yaxis.axis_label = 'Celsius'
	p.legend.location = "bottom_left"
	p.legend.click_policy="hide"

	p.extra_y_ranges = {"hum": Range1d(start=0, end=100)}
	p.add_layout(LinearAxis(y_range_name="hum", axis_label='%'), 'right')
	p.line('dates', 'relative_humidity_set_1', source=source, legend = 'Rel Hum', line_color="green" , y_range_name="hum")

	p1 = figure(plot_height=300, plot_width=800,
	            x_range=p.x_range,
	            # title="Richardson @ Trims DOT (TRDA2)",
	           x_axis_type="datetime", x_axis_location="above",
	           background_fill_color="#efefef")
	# tools="xpan", toolbar_location=None
	p1.line('dates', 'wind_speed_set_1', source=source, legend = 'Wind speed', line_color="tomato")
	p1.line('dates', 'wind_gust_set_1', source=source, legend = 'Gusts', line_color="indigo" )
	p1.y_range = Range1d(start=0, end= dat_df.wind_gust_set_1.max() +2)

	p1.yaxis.axis_label = 'm/s'

	p1.legend.location = "bottom_left"
	p1.legend.click_policy="hide"

	p1.extra_y_ranges = {"dir": Range1d(start=0, end=360)}
	p1.add_layout(LinearAxis(y_range_name="dir"), 'right')
	p1.circle('dates', 'wind_direction_set_1', source=source, legend = 'Wind Dir', line_color="black" , y_range_name="dir")




	select = figure(title="Drag the selection box to change the range above",
	                plot_height=130, plot_width=800, y_range=p.y_range,
	                x_axis_type="datetime",
	                tools="", toolbar_location=None, background_fill_color="#efefef", x_range=(dates[0], dates[-1]))

	range_tool = RangeTool(x_range=p.x_range)
	range_tool.overlay.fill_color = "navy"
	range_tool.overlay.fill_alpha = 0.2

	select.line('dates', 'air_temp_set_1', source=source)
	select.extra_y_ranges = {"pcp": Range1d(start=0, end=5)}
	select.yaxis.axis_label = 'C'
	select.add_layout(LinearAxis(y_range_name="pcp", axis_label='mm'), 'right')
	select.vbar(x='dates', top='precip_accum_24_hour_set_1', source=source, width=1, y_range_name="pcp")
	select.ygrid.grid_line_color = None
	select.add_tools(range_tool)
	select.toolbar.active_multi = range_tool

	return(column(p, p1, select))

@app.route('/')
def trimsDOT():
	# Create the plot
	plot = StationPlot('TRDA2')
		
	# Embed plot into HTML via Flask Render
	script, div = components(plot)
	return render_template("TrimsDot.html", script=script, div=div)



@app.route('/blackRapids/')
def blackRapids():
	# Create the plot
	plot = StationPlot('BKCA2')
		
	# Embed plot into HTML via Flask Render
	script, div = components(plot)
	return render_template("BlackRapids.html", script=script, div=div)


# @app.route('/')
# def home():
	
#     return render_template('home.html')

# @app.route('/BlackRapids/')
# def BlackRapids():

# 	now = datetime.datetime.now()

# 	end = str(now.year) + fixdatestrings(now.month) + fixdatestrings(now.day) + fixdatestrings(now.hour)
# 	startdate = date.today() - timedelta(30)
# 	start = str(startdate.year) + fixdatestrings(startdate.month) + fixdatestrings(startdate.day)
# 	# print(start)
# 	# print (end)
# 	# 201904240000

# 	var = 'vars=pressure,air_temp,dew_point_temperature,relative_humidity,wind_speed,wind_direction,wind_gust,precip_accum,precip_accum_24_hour'

# 	filename ='https://api.mesowest.net/v2/stations/timeseries?&stid=BKCA2&start='+start+'0000&end='+end+'00&token=demotoken&r&obtimezone=local&'+var+'&output=csv'
# 	dat_df = read_files(filename) #load json and turn into dataframe.

# 	dates = np.array(dat_df.Date_Time , dtype=np.datetime64)
# 	dat_df['dates'] = np.array(dat_df.Date_Time , dtype=np.datetime64)
# 	source = ColumnDataSource(data=dat_df)
# 	# source = ColumnDataSource(data=dict(date=dates, temp=dat_df.air_temp_set_1, dew = dat_df.dew_point_temperature_set_1d))
# 	# print(dat_df.head())
# 	p = figure(plot_height=300, plot_width=800,
# 	            title="Black Rapids (BKCA2)",
# 	           x_axis_type="datetime", x_axis_location="above",
# 	           background_fill_color="#efefef", x_range=(dates[-200], dates[-1]))
# 	# tools="xpan", toolbar_location=None
# 	p.line('dates', 'air_temp_set_1', source=source, legend = 'Air Temp', line_color="tomato")
# 	p.line('dates', 'dew_point_temperature_set_1d', source=source, legend = 'Dew Point', line_color="indigo" )
# 	p.y_range = Range1d(
# 	    dat_df.dew_point_temperature_set_1d.min() , dat_df.air_temp_set_1.max() +2)

# 	p.yaxis.axis_label = 'Celsius'
# 	p.legend.location = "bottom_left"
# 	p.legend.click_policy="hide"

# 	p.extra_y_ranges = {"hum": Range1d(start=0, end=100)}
# 	p.add_layout(LinearAxis(y_range_name="hum", axis_label='%'), 'right')
# 	p.line('dates', 'relative_humidity_set_1', source=source, legend = 'Rel Hum', line_color="green" , y_range_name="hum")

# 	p1 = figure(plot_height=300, plot_width=800,
# 	            x_range=p.x_range,
# 	            # title="Richardson @ Trims DOT (TRDA2)",
# 	           x_axis_type="datetime", x_axis_location="above",
# 	           background_fill_color="#efefef")
# 	# tools="xpan", toolbar_location=None
# 	p1.line('dates', 'wind_speed_set_1', source=source, legend = 'Wind speed', line_color="tomato")
# 	p1.line('dates', 'wind_gust_set_1', source=source, legend = 'Gusts', line_color="indigo" )
# 	p1.y_range = Range1d(start=0, end= dat_df.wind_gust_set_1.max() +2)

# 	p1.yaxis.axis_label = 'm/s'

# 	p1.legend.location = "bottom_left"
# 	p1.legend.click_policy="hide"

# 	p1.extra_y_ranges = {"dir": Range1d(start=0, end=360)}
# 	p1.add_layout(LinearAxis(y_range_name="dir"), 'right')
# 	p1.circle('dates', 'wind_direction_set_1', source=source, legend = 'Wind Dir', line_color="black" , y_range_name="dir")




# 	select = figure(title="Drag the selection box to change the range above",
# 	                plot_height=130, plot_width=800, y_range=p.y_range,
# 	                x_axis_type="datetime",
# 	                tools="", toolbar_location=None, background_fill_color="#efefef", x_range=(dates[0], dates[-1]))

# 	range_tool = RangeTool(x_range=p.x_range)
# 	range_tool.overlay.fill_color = "navy"
# 	range_tool.overlay.fill_alpha = 0.2

# 	select.line('dates', 'air_temp_set_1', source=source)
# 	#select.extra_y_ranges = {"pcp": Range1d(start=0, end=5)}
# 	select.yaxis.axis_label = 'C'
# 	select.add_layout(LinearAxis(y_range_name="pcp", axis_label='mm'), 'right')
# 	#select.vbar(x='dates', top='precip_accum_24_hour_set_1', source=source, width=1, y_range_name="pcp")
# 	select.ygrid.grid_line_color = None
# 	select.add_tools(range_tool)
# 	select.toolbar.active_multi = range_tool
# 	#show(p)

# 	html1 = file_html(column(p, p1, select), CDN, "Black Rapids")
# 	Html_file1= open("App/templates/BlackRapids.html","w")
# 	Html_file1.write(html1)
# 	Html_file1.close()
# 	# output_file("templates/plotMesowest.html")


# 	return render_template('BlackRapids.html')




if __name__ == '__main__':
#    app.run(debug=True)
    app.run(host='0.0.0.0')