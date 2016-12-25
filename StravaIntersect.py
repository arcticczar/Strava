# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 10:44:27 2016

@author: MStelmach
"""

import os

from osgeo import ogr, osr

# ++++++++++++++++++++++++++++++++++++
#Define input and output
input_shapefile = r'H:/MyDocuments/UW/CapstoneProject/NatCapData/FinalData/MBSStravaSegmentsFROMJSON20160723projected.shp'
intersectWith = r'H:/MyDocuments/UW/CapstoneProject/NatCapData/FinalData/trailbuffer500mProjected.shp'
output = r'H:\MyDocuments\UW\CapstoneProject\NatCapData\FinalData\TrailBufferStravaData.shp'
#+++++++++++++++++++++++++++++++++++++

#Get GDAL Shapefile driver
driver = ogr.GetDriverByName("ESRI Shapefile")
srs = osr.SpatialReference()

print 'input shapefile', os.path.exists(input_shapefile)
print 'intersect shapefile', os.path.exists(intersectWith)

#Open the trails buffer shapefile in read only mode
dsTrailBuffer = driver.Open(intersectWith, 0)
lyrTrailBuffer = dsTrailBuffer.GetLayer()
lyrdefTrailBuffer = lyrTrailBuffer.GetLayerDefn()
trailfeat = lyrTrailBuffer.GetNextFeature()
#Copy the trail geometry
trailgeom = trailfeat.geometry().Clone()

#Get the spatial reference
TBproj = lyrTrailBuffer.GetSpatialRef()

#Copy the schema of the input 
schema  = lyrTrailBuffer.schema


#Open the strava data in read only mode
dsStrava = driver.Open(input_shapefile, 0)
lyrStrava = dsStrava.GetLayer()
stravafeat = lyrStrava.GetNextFeature()
stravageom = stravafeat.geometry().Clone()

#Get the spatial reference and save as WKT
lyrdefStrava = lyrStrava.GetLayerDefn()
Sproj = lyrStrava.GetSpatialRef()
srs = Sproj.ExportToWkt()

#create the output shapefile
if os.path.exists(output):
    driver.DeleteDataSource(output)
dsOutput = driver.CreateDataSource(output)

#set the spatial reference from the input
insrs = osr.SpatialReference()
insrs.ImportFromWkt(srs)

#Create the shapefile in memory
outlayer = dsOutput.CreateLayer(output, insrs, ogr.wkbMultiPolygon)

#Copy fields from the input intersect shapefile
outlayer.CreateFields(schema)

#Add fields for average use rate per year and strava segments
outlayer.CreateField(ogr.FieldDefn("Use_Rate", ogr.OFTReal))
outlayer.CreateField(ogr.FieldDefn("SSegCount", ogr.OFTInteger))
outdef = outlayer.GetLayerDefn()
outfeature = ogr.Feature(outdef)


for feature in lyrTrailBuffer:
    for field in range(feature.GetFieldCount()):
	#Set fields of the output equal to the input intersection layer        
	value = feature.GetField(field)
        outfeature.SetField(field, value)
    trailgeom = feature.geometry()
    outfeature.SetGeometry(trailgeom)
    #Start with 0 segments and 0 use rate
    ssegcount = 0
    userate = 0
    for item in lyrStrava:
        stravageom = item.geometry()
        #return all segments that intersect
        if not trailgeom.Intersect(stravageom):
            #add the use rate to total use rate
            userate += item.GetField('Use_Rate')
            #Add one to the number of Strava segments included
            ssegcount +=1

    #Add fields to output shapefile    
    outfeature.SetField("Use_Rate", userate)
    outfeature.SetField("SSegCount", ssegcount)
    outlayer.CreateFeature(outfeature)
    lyrStrava.ResetReading()     

#Close all open data sets/layers and save to file.

dsTrailBuffer.Destroy()
dsStrava.Destroy()
dsOutput.Destroy()
