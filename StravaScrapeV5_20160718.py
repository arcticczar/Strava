# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 19:42:05 2016

@author: MStelmach
"""

import stravalib
import requests
import datetime
import polyline
import time
import types
from osgeo import ogr
from math import ceil
import sys, os
import json

#Get current time
starttime = datetime.datetime.now()
scriptstart = starttime

#Define the bounding box for strava search
#Example: Bounds = r"H:\MyDocuments\UW\CapstoneProject\GIS_Background\adminown\adminownprojected.shp"
#Example 2: Bounds = [-122.19401695785098, 46.874837987936324, -120.90679054890244, 48.99982719694641]
def BoundingBox(Bounds):
    global bbox
    #input either SW and NE corner as a length 4 list or a shapefile in WGS84
    if type(Bounds) == types.StringType:
        try:
            driver = ogr.GetDriverByName('ESRI Shapefile')
            ds = driver.Open(Bounds)
            if ds:
                layer = ds.GetLayerByIndex(0)
                extent  = layer.GetExtent()
                #print extent
                bbox = {'LonMin':extent[0], 'LatMin':extent[2], 'LonMax':extent[1], 'LatMax':extent[3]} #SW and NE corners
                ds.Destroy()
            else:
                sys.exit("Input not appropriate Shapefile: operation canceled")
        except:
            sys.exit("Input not Shapefile: operation canceled")
    elif type(Bounds) == types.ListType and len(Bounds)==4:
        bbox = {'LonMin':Bounds[0], 'LatMin':Bounds[1], 'LonMax':Bounds[2], 'LatMax':Bounds[3]}
    for item in bbox:
        if bbox[item]>180 or bbox[item]<-180:
            print 'Warning Bounds must be in WGS84 decimal degrees'    

    #bounding box
    global LatMin, LatMax, LonMin, LonMax
    LatMin = bbox['LatMin']
    LatMax = bbox['LatMax']
    LonMin = bbox['LonMin']
    LonMax = bbox['LonMax']
    
    latcount = (abs(LatMax-LatMin))/0.01
    loncount = (abs(LonMax-LonMin))/0.01
    totalCells = ceil(latcount)*ceil(loncount)
    processtime = totalCells/30000
    
    
    if totalCells > 20000:
        print '{0} cells in area, processing time {1} or more days (depending on trail density). '.format (totalCells, processtime)
        print '30,000 API Calls per day maximum'
    
    return [LonMin, LatMin, LonMax, LatMax]

AOI = BoundingBox(r"H:\MyDocuments\UW\CapstoneProject\GIS_Background\adminown\adminownprojected.shp")
print bbox

workingdir = r'H:\MyDocuments\UW\CapstoneProject\Scripts\Working'
if not os.path.exists(workingdir):
    os.mkdir(workingdir)

tempfile = os.path.join(workingdir + 'stravasegments20160721.txt')

#Stravalib client identification
AccessToken = ""
client = stravalib.client.Client()
client.access_token = AccessToken

#Bounding box tracking file
def boundfiletracker(starttime, workingdir, bounds, bbox, dist):
    
    tracker = {}
    boundfiletracker = open(os.path.join(workingdir + 'LastBoundingBox.txt'), 'w')
    tracker['StartTime'] = starttime.isoformat()
    tracker['CurrentTime'] = datetime.datetime.now().isoformat()
    tracker['currentbox'] = {'boxLatMin':bounds[0], 'boxLonMin':bounds[1], 'boxLatMax':bounds[2], 'boxLonMax':bounds[3]}
    tracker['extent'] = bbox
    tracker['dist'] = dist
    boundfiletracker.write(json.dumps(tracker))
    boundfiletracker.close()

    
# create an empty set for segment ID numbers, and counters for row, column, and count of empty lists
segmentlist = set()
emptylistcount =0
row =1
count = 0
calls = 0
dist = 0.05
LatMinOriginal = LatMin
LonMinOriginal = LonMin
latmax = abs(LatMax-LatMin)
lonmax = abs(LonMax-LonMin)
if latmax>lonmax:
    maxdist = latmax
else:
    maxdist = lonmax


MBSStrava = {}
#start searching from the southwest and work north by 0.01 decimal degree
# when the latitude exceeds the max, restart at lat min and shift east 0.01 deg
while dist<maxdist:
    
    while (LatMin+(dist/2))<LatMax or (LonMin+(dist/2))<LonMax: #if (LatMin + dist)< LatMax all results will be inside bounds 
        if (LatMin+dist/2)<LatMax:
            #search an area just large enough to contain the largest running segments
            bounds = [LatMin, LonMin, LatMin+dist, LonMin+dist]
            boundfiletracker(starttime, workingdir, bounds, bbox, dist)
                
            time.sleep(4) # trying to avoid the 30000/day limit, but 3 was not long enough.
            try:
                calls +=1
                for item in client.explore_segments(bounds):
                    
                    #if the item exists and has not already been scraped, scrape data
                    if item and item.id not in segmentlist:
                        SegmentID = item.id #unique ID number
                        print 'New segment ID: ', SegmentID
                        segmentlist.add(SegmentID)
                        SegmentName = item.name #segment name
                        calls +=1
                        #print SegmentName
                        try:
                            SegDetails = client.get_segment(SegmentID)
                            usetype = SegDetails.activity_type
                            #print calls
                            creationdate = SegDetails.created_at #Date the segment was uploaded to strava
                            creationdate = creationdate.replace(tzinfo=None)
                            #print 'creation date ', creationdate
                            #print creationdate.strftime('%Y%m%d'),type(creationdate.strftime('%Y%m%d'))
                            effortcount = SegDetails.effort_count #efforts between creation date and collection date
                            #print 'effort count' , effortcount
                            athletecount = SegDetails.athlete_count #number of athletes who have tried the segment
                            timedelt = starttime-creationdate
                            TimeDelt = timedelt.total_seconds()
                            yrs = TimeDelt/(60*60*24*365) #convert seconds to years
                            #print yrs, type(yrs)
                            if yrs:
                                userate = float(effortcount)/yrs #Efforts per year as 'userate'
                                
                                #print userate
                            else:
                                userate = 0.0
                            #print 'use rate ', userate
                            line  = SegDetails.map.polyline
                            #print line
                            shape = polyline.decode(line) #google polyline encoding as a string decode with polyline lib
                            #print shape                        
                            if shape:
                                wkt = ogr.Geometry(ogr.wkbLineString)
                                for item in shape:
                                    wkt.AddPoint(item[1],item[0])
                                #Create a list with all attributes.
                                #info = [, SegmentID, creationdate.strftime('%Y%m%d'), int(effortcount), int(athletecount), yrs, userate, wkt]
                                
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
                                s = json.dumps(MBSStrava)
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
            print 'sleep'
            time.sleep(4) # trying to avoid the 30000/day limit, but 3 was not long enough.
            LatMin = LatMinOriginal
            LonMin += (dist/5)
            row +=1
            print 'New Row: ' , row
            print 'lat, long : ' , LatMin, LonMin
            print 'count : ' , count 
            print bounds
            print datetime.datetime.now()
            boundfiletracker(starttime, workingdir, bounds, bbox, dist)
    dist = dist*2
    LatMin = LatMinOriginal
    LonMin = LonMinOriginal
#writefile.close()
#data_source.Destroy()
