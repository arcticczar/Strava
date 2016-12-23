# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 06:33:00 2016

@author: MStelmach
"""

from osgeo import ogr,osr
import simplejson

#Define input and output
input_file = 'H:\MyDocuments\UW\CapstoneProject\scripts\workingstravasegments20160724.txt'
output_shapefile = 'H:\MyDocuments\UW\CapstoneProject\NatCapData\Strava\MBSStravaSegmentsFROMJSON20160726.shp'

#Read text file input from Strava Scraper
reader = open(input_file, 'r')

#read the json into memory
segmentdict = simplejson.loads(reader.read())

fmt = '%Y-%m-%dT%H:%M:%S.%f' #iso date format input

#set working parameters for ogr
driver = ogr.GetDriverByName("ESRI Shapefile")
srs = osr.SpatialReference()
srs.SetWellKnownGeogCS("WGS84") #WGS 84 decimal degrees http://spatialreference.org/ref/epsg/wgs-84/

#create driver for shapefile creation
data_source = driver.CreateDataSource(output_shapefile)
layer = data_source.CreateLayer("StravaSegs", srs, ogr.wkbMultiLineString)

#Create fields for new shapefile
#Set name field
field_name = ogr.FieldDefn("Name", ogr.OFTString)
field_name.SetWidth(50)
layer.CreateField(field_name) #Create name field
#Set segment ID field
field_StravaID = ogr.FieldDefn( "StravaID", ogr.OFTInteger)
field_StravaID.SetWidth(12)
layer.CreateField(field_StravaID)#Create segment ID
#Set use type (run or cycle)
field_useType = ogr.FieldDefn( "UseType", ogr.OFTString)
field_useType.SetWidth(12)
layer.CreateField(field_useType)#Create use type
#Set Creation Date (date segment was created)
field_CreateDate = ogr.FieldDefn("C_Date", ogr.OFTInteger)
layer.CreateField(field_CreateDate) #Create Creation Date
#Set timedelta field (difference between time created
#and time the segment was scraped).
field_TimeDelt = ogr.FieldDefn("TimeDelt", ogr.OFTReal)
layer.CreateField(field_TimeDelt)#Create timedelta
#Create efforts field (count of segment uses)
layer.CreateField(ogr.FieldDefn("Efforts", ogr.OFTInteger))
#Create use rate field (uses/total time)
layer.CreateField(ogr.FieldDefn("Use_Rate", ogr.OFTReal))
#Athelete count field(number of users)
layer.CreateField(ogr.FieldDefn("Ath_Cnt", ogr.OFTInteger))
#Boundary box
field_bounds = ogr.FieldDefn("Bounds", ogr.OFTString)
field_bounds.SetWidth(100)
layer.CreateField(field_bounds) #create bounding box
layer.CreateField(ogr.FieldDefn("Dist", ogr.OFTReal))

#Read lines from well known text into shapefile
for line in segmentdict:
    this = segmentdict[line]
    wkt = this['wkt'] #return the coordinates within the list

    #test to see the file has an associated shape
    if wkt:
	#If the segment exists, create a feature from the dictionary
        athletes = this['athletecount']
        usetype = this['usetype']
        efforts = this['effortcount']
        creationdate = this['creationdate']
        yrs = this['years'] #convert seconds to years
        userate = this['userate']
        SegID = this['segmentID']
        segmentName = this['name']
        bounds = str(this['bounds'])
        dist = this['dist']

        #Set feature attributes          
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField("Name", segmentName)
        feature.SetField("StravaID", SegID)
        feature.SetField("UseType", usetype)
        feature.SetField("C_Date", creationdate)
        feature.SetField("TimeDelt", yrs)
        feature.SetField("Efforts", efforts)
        feature.SetField("Use_Rate", userate)
        feature.SetField("Ath_Cnt", athletes)
        feature.SetField("Bounds", bounds)
        feature.SetField("Dist", dist)

        #Create line segments
        polyline = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(polyline) #Set geometry to of line feature
        layer.CreateFeature(feature) #Create in shapefile
        feature.Destroy() #remove to free resources
        layer.SyncToDisk()
        data_source.SyncToDisk()

reader.close()
data_source.Destroy()
