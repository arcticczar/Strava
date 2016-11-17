# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 06:33:00 2016

@author: MStelmach


"""

from osgeo import ogr,osr
import simplejson

input_file = 'H:\MyDocuments\UW\CapstoneProject\scripts\workingstravasegments20160724.txt'
output_shapefile = 'H:\MyDocuments\UW\CapstoneProject\NatCapData\Strava\MBSStravaSegmentsFROMJSON20160726.shp'

reader = open(input_file, 'r')

segmentdict = simplejson.loads(reader.read())

fmt = '%Y-%m-%dT%H:%M:%S.%f' #iso date format input

driver = ogr.GetDriverByName("ESRI Shapefile")
srs = osr.SpatialReference()
srs.SetWellKnownGeogCS("WGS84") #WGS 84 decimal degrees http://spatialreference.org/ref/epsg/wgs-84/

data_source = driver.CreateDataSource(output_shapefile)
layer = data_source.CreateLayer("StravaSegs", srs, ogr.wkbMultiLineString)

field_name = ogr.FieldDefn("Name", ogr.OFTString)
field_name.SetWidth(50)
layer.CreateField(field_name)
field_StravaID = ogr.FieldDefn( "StravaID", ogr.OFTInteger)
field_StravaID.SetWidth(12)
layer.CreateField(field_StravaID)
field_useType = ogr.FieldDefn( "UseType", ogr.OFTString)
field_useType.SetWidth(12)
layer.CreateField(field_useType)
field_CreateDate = ogr.FieldDefn("C_Date", ogr.OFTInteger)
layer.CreateField(field_CreateDate)
field_TimeDelt = ogr.FieldDefn("TimeDelt", ogr.OFTReal)
layer.CreateField(field_TimeDelt)
layer.CreateField(ogr.FieldDefn("Efforts", ogr.OFTInteger))
layer.CreateField(ogr.FieldDefn("Use_Rate", ogr.OFTReal))
layer.CreateField(ogr.FieldDefn("Ath_Cnt", ogr.OFTInteger))
field_bounds = ogr.FieldDefn("Bounds", ogr.OFTString)
field_bounds.SetWidth(100)
layer.CreateField(field_bounds)
layer.CreateField(ogr.FieldDefn("Dist", ogr.OFTReal))

for line in segmentdict:
    this = segmentdict[line]
    wkt = this['wkt'] #return the coordinates within the list
    if wkt:
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

        polyline = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(polyline) #Set geometry to of line feature
        layer.CreateFeature(feature) #Create in shapefile
        feature.Destroy() #remove to free resources
        layer.SyncToDisk()
        data_source.SyncToDisk()

reader.close()
data_source.Destroy()