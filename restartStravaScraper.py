# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 20:53:01 2016

@author: MStelmach
This file uses decimal degrees from WGS 84 which will lead to distorted squares.
This was sufficient for the use created, verify your use case.
"""

import polyline
import simplejson
import datetime
from osgeo import ogr
import stravalib
import time
import requests
import sys

starttime = datetime.datetime.now()

#++++++++++++++++++++++++++++++++++++++++++++++++
#Set your previous working directory to resume
workingdir = 'H:\MyDocuments\UW\CapstoneProject\Scripts\Working'

previous_JSON = workingdir + '\lastboundingbox.txt'#ADD YOUR PREVIOUS TRACKING OUTPUT

tempfile = workingdir + '\stravasegments20160721.txt'  #ADD YOUR PREVIOUS OUTPUT
#++++++++++++++++++++++++++++++++++++++++++++++++
jsonreader = open(previous_JSON, 'r')

reader = jsonreader.read()

print reader, type(reader)

#Read from the previous file into memory
stats = simplejson.loads(reader)

#Read previous run into memory to continue.
lastrunstart = stats['StartTime'] 
lastrunend = stats['CurrentTime']
currentbox = stats['currentbox']
extent = stats['extent']
dist = stats['dist']

jsonreader.close()

#Confirm the start time of the last run
lastend = datetime.datetime.strptime(lastrunend,'%Y-%m-%dT%H:%M:%S.%f') 
laststart = datetime.datetime.strptime(lastrunstart,'%Y-%m-%dT%H:%M:%S.%f')
lastruntime = lastend-laststart
print 'last run time (hours) :', lastruntime.total_seconds()/(60*60)
deltadate = starttime.date() - lastend.date()
deltadate = deltadate.total_seconds()/(60*60*24)
print deltadate, 'days since last run'

#Create a bounding box for the current area
LatMin = currentbox['boxLatMin']
LatMax = currentbox['boxLatMax']
LonMin = currentbox['boxLonMin']
LonMax = currentbox['boxLonMax']

#Create a bounding box for the entire area
LatMinOriginal = extent['LatMin']
LatMaxOriginal = extent['LatMax']
LonMinOriginal = extent['LonMin']
LonMaxOriginal = extent['LonMax']


#Stravalib client identification
AccessToken = "" #ADD YOUR ACCESS TOKEN
client = stravalib.client.Client()
client.access_token = AccessToken

#Bounding box tracking file, allows for restarting.
def boundfiletracker(starttime, workingdir, bounds, bbox, dist):
    
    tracker = {}
    boundfiletracker = open(workingdir + '\LastBoundingBox.txt', 'w')
    tracker['StartTime'] = starttime.isoformat()
    tracker['CurrentTime'] = datetime.datetime.now().isoformat()
    tracker['currentbox'] = {'boxLatMin':bounds[0],
                             'boxLonMin':bounds[1],
                             'boxLatMax':bounds[2],
                             'boxLonMax':bounds[3]}
    tracker['extent'] = bbox
    tracker['dist'] = dist
    boundfiletracker.write(simplejson.dumps(tracker))
    boundfiletracker.close()
    
# create an empty set for segment ID numbers, 
# and counters for row, column, and count of empty lists
segmentlist = set()
emptylistcount =0
row =1
count = 0
calls = 0

#Return the length of the bounding box sides
latmax = abs(LatMaxOriginal-LatMinOriginal)
lonmax = abs(LonMaxOriginal-LonMinOriginal)

#Return the length of the longest side 
#to bound the expansion of search boxes
if latmax>lonmax:
    maxdist = latmax
else:
    maxdist = lonmax

#start searching from the southwest and work north by (dist) decimal degree
# when the latitude exceeds the max, restart at lat min and shift east 0.01 deg
while dist<maxdist:
    
    while LatMin<LatMaxOriginal or LonMin<LonMaxOriginal:
        if LatMin<LatMaxOriginal:
            #search an area just large enough to contain the largest running segments
            bounds = [LatMin, LonMin, LatMin+dist, LonMin+dist]
            boundfiletracker(starttime, workingdir, bounds, extent, dist)
            
            if calls >= 30000:
                timedif = datetime.datetime(starttime.year, starttime.month, starttime.day+1)-starttime
                if timedif.total_seconds() < 0:
                    calls = 0
                    starttime = datetime.datetime.now()
                elif timedif.total_seconds()>0:
                    time.sleep(timedif.total_seconds())
                    calls = 0
                    starttime = datetime.datetime.now()
                
            time.sleep(4) # trying to avoid the 30000/day limit, but 3 was not long enough.
            try:
                calls +=1
                for item in client.explore_segments(bounds):
                    
                    #if the item exists and has not already been scraped, scrape data
                    if item and str(item.id) not in MBSStrava:
                        SegmentID = item.id #unique ID number
                        print 'New segment ID: ', SegmentID
                        
                        SegmentName = item.name #segment name
                        calls +=1
                        
                        try:
                            SegDetails = client.get_segment(SegmentID)
                            usetype = SegDetails.activity_type
                            
                            #Date the segment was uploaded to strava
                            creationdate = SegDetails.created_at 
                            creationdate = creationdate.replace(tzinfo=None)

                            #efforts between creation date and collection date
                            effortcount = SegDetails.effort_count

                            #number of athletes who have tried the segment
                            athletecount = SegDetails.athlete_count

                            #Time between creation and current
                            timedelt = starttime-creationdate
                            TimeDelt = timedelt.total_seconds()
                            yrs = TimeDelt/(60*60*24*365) #convert seconds to years
                            
                            if yrs:
                                userate = float(effortcount)/yrs #Efforts per year as 'userate'
                                
                                
                            else:
                                userate = 0.0
                            
                            line  = SegDetails.map.polyline
                            
                            #google polyline encoding as a string decode with polyline lib
                            shape = polyline.decode(line)
                                                   
                            if shape:
                                wkt = ogr.Geometry(ogr.wkbLineString)
                                for item in shape:
                                    wkt.AddPoint(item[1],item[0])
                                #Create a dictionary with all attributes.
                                                                
                                MBSStrava[str(SegmentID)]={'name': SegmentName,
                                                           'segmentID': int(SegmentID), 
                                                           'usetype': usetype,
                                                           'creationdate': int(creationdate.strftime('%Y%m%d')),
                                                           'effortcount':int(effortcount),
                                                           'athletecount':int(athletecount),
                                                           'years':float(yrs),
                                                           'userate':float(userate),
                                                           'wkt':str(wkt),
                                                           'bounds':bounds,
                                                           'dist': dist}
                                writefile = open(tempfile, 'w')
                                s = simplejson.dumps(MBSStrava)
                                writefile.write(s)
                                writefile.close()
                                print len(MBSStrava), 'segments read'
                                                                                                              
                                
                        except requests.exceptions.HTTPError:
                            print 'Rate Exceeded, waiting 1 minute', datetime.datetime.now()
                            print bounds
                            time.sleep(60)
                            continue
                        except stravalib.exc.RateLimitExceeded:
                            print 'Rate Exceeded, waiting 1 minute', datetime.datetime.now()
                            print bounds
                            time.sleep(60)
                            continue
                        except KeyboardInterrupt:
                            break
                        except:
                            print 'Other exception occurred:', sys.exc_info()
                            break
                        
                    else:
                        if item:
                            try:
                                print item.id , 'already contained in segmentlist'
                            except ValueError:
                                print 'Value Error Exception on a duplicate segment'
                            except:
                                print 'Other exception on a duplicate segment', sys.exc_info()[0]
                        else:
                            print 'empty list:', emptylistcount
                LatMin += (dist/5)
                count +=1
                print 'row:',row, ' , count:', count, 'calls:', calls, 'dist:', dist, 'bounds:', bounds
            except requests.exceptions.HTTPError:
                print 'Rate Exceeded, waiting 1 minute', datetime.datetime.now()
                time.sleep(60)
                LastBox = bounds
                print 'last sample area: ', str(bounds)
                continue
            
            except stravalib.exc.RateLimitExceeded:
                print 'Rate Exceeded, waiting 1 minute', datetime.datetime.now()
                LastBox = bounds
                print bounds
                time.sleep(60)
                continue
            except KeyboardInterrupt:
                #data_source.Destroy()
                break
            except:
                print 'Other exception occurred:', sys.exc_info()
                #data_source.Destroy()
                break              
                
        else: #when all latitudes have been searched restart at the south and shift east
            #print 'sleep'
            time.sleep(4) # trying to avoid the 30000/day limit, but 3 was not long enough.
            LatMin = LatMinOriginal
            LonMin += (dist/5)
            row +=1
            print 'New Row: ' , row
            print 'lat, long : ' , LatMin, LonMin
            print 'count : ' , count 
            print bounds
            print datetime.datetime.now()
            boundfiletracker(starttime, workingdir, bounds, extent, dist)
    #Double the distance and repeat until the distance exceeds the length of the longer side.
    dist = dist*2
    LatMin = LatMinOriginal
    LonMin = LonMinOriginal
#writefile.close()
#data_source.Destroy()
