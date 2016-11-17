# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 10:44:27 2016

@author: MStelmach
"""

import os
from osgeo import ogr, osr
#from collections import Counter

input_shapefile = r'H:/MyDocuments/UW/CapstoneProject/NatCapData/FinalData/MBSStravaSegmentsFROMJSON20160723projected.shp'
intersectWith = r'H:/MyDocuments/UW/CapstoneProject/NatCapData/FinalData/trailbuffer500mProjected.shp'
output = r'H:\MyDocuments\UW\CapstoneProject\NatCapData\FinalData\TrailBufferStravaData.shp'

driver = ogr.GetDriverByName("ESRI Shapefile")
srs = osr.SpatialReference()

print 'input shapefile', os.path.exists(input_shapefile)
print 'intersect shapefile', os.path.exists(intersectWith)

#Open the trails buffer shapefile in read only mode
dsTrailBuffer = driver.Open(intersectWith, 0)
lyrTrailBuffer = dsTrailBuffer.GetLayer()
lyrdefTrailBuffer = lyrTrailBuffer.GetLayerDefn()
trailfeat = lyrTrailBuffer.GetNextFeature()
trailgeom = trailfeat.geometry().Clone()
#for i in range(lyrdefTrailBuffer.GetFieldCount()):
#    print lyrdefTrailBuffer.GetFieldDefn(i).GetName()
TBproj = lyrTrailBuffer.GetSpatialRef()
schema  = lyrTrailBuffer.schema


#Open the strava data in read only mode
dsStrava = driver.Open(input_shapefile, 0)
lyrStrava = dsStrava.GetLayer()
stravafeat = lyrStrava.GetNextFeature()
stravageom = stravafeat.geometry().Clone()
lyrdefStrava = lyrStrava.GetLayerDefn()
#for i in range(lyrdefStrava.GetFieldCount()):
#    print lyrdefStrava.GetFieldDefn(i).GetName()
Sproj = lyrStrava.GetSpatialRef()
srs = Sproj.ExportToWkt()

#create the output shapefile
if os.path.exists(output):
    driver.DeleteDataSource(output)
dsOutput = driver.CreateDataSource(output)
insrs = osr.SpatialReference()
insrs.ImportFromWkt(srs)
#data_source = driver.CreateDataSource(output)
outlayer = dsOutput.CreateLayer(output, insrs, ogr.wkbMultiPolygon)
outlayer.CreateFields(schema)

outlayer.CreateField(ogr.FieldDefn("Use_Rate", ogr.OFTReal))
outlayer.CreateField(ogr.FieldDefn("SSegCount", ogr.OFTInteger))
outdef = outlayer.GetLayerDefn()
outfeature = ogr.Feature(outdef)


for feature in lyrTrailBuffer:
    for i in range(feature.GetFieldCount()):
        value = feature.GetField(i)
        outfeature.SetField(i, value)
    trailgeom = feature.geometry()
    outfeature.SetGeometry(trailgeom)
    ssegcount = 0
    userate = 0
    for item in lyrStrava:
        stravageom = item.geometry()
        if not trailgeom.Intersect(stravageom):
            userate += item.GetField('Use_Rate')
            ssegcount +=1

        
    outfeature.SetField("Use_Rate", userate)
    outfeature.SetField("SSegCount", ssegcount)
    outlayer.CreateFeature(outfeature)
    lyrStrava.ResetReading()     

#Close all open data sets/layers

dsTrailBuffer.Destroy()
dsStrava.Destroy()
dsOutput.Destroy()