# -*- coding: utf-8 -*-
"""
Creating a buffer for polyline trail data via open source ogr.
Created on Thu Jun 30 17:46:56 2016
Draws from:
https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#create-buffer
https://github.com/OSGeo/gdal/blob/trunk/gdal/swig/python/samples/gdalcopyproj.py
 
@author: MStelmach
"""

import os
import shutil

import ogr

#Set input shapefile and output
daShapefile = r"H:\MyDocuments\UW\CapstoneProject\NatCapData\from_dave-2016-07-22\from_dave\mbs_trails_infra-grouped_v3\mbs_trails_infra-grouped_v3.shp"
output = r"H:\MyDocuments\UW\CapstoneProject\NatCapData\FinalData\trailbuffer500m.shp"

# Input Feature name, Output or Buffered Feature name, Buffer Distance
def createBuffer(inputfn, outputBufferfn, bufferDist):
    #Set data source - input data  
    inputds = ogr.Open(inputfn)
    inputlyr = inputds.GetLayer()
    inputlyrdef = inputlyr.GetLayerDefn()
    
    #Determine if the file name already exists.  If it exists it will be deleted
    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(outputBufferfn):
        shpdriver.DeleteDataSource(outputBufferfn)
        
    #Create a new polygon shapefile    
    outputBufferds = shpdriver.CreateDataSource(outputBufferfn)
    bufferlyr = outputBufferds.CreateLayer(outputBufferfn, geom_type=ogr.wkbPolygon)
    
    
    
    #read fields in input file
    fieldlist = []
    for i in range(inputlyrdef.GetFieldCount()):
        #get input field properties
        fieldname =  inputlyrdef.GetFieldDefn(i).GetName()
        fieldTypeCode = inputlyrdef.GetFieldDefn(i).GetType()
        fieldWidth = inputlyrdef.GetFieldDefn(i).GetWidth()
        Getprecision = inputlyrdef.GetFieldDefn(i).GetPrecision()
        
        #read fields into new field holder fieldlist
        fieldlist.append(fieldname)
        
        newfield = ogr.FieldDefn(fieldname, fieldTypeCode)
        newfield.SetWidth(fieldWidth)
        newfield.SetPrecision(Getprecision)
        bufferlyr.CreateField(newfield)
    
    featureDefn = bufferlyr.GetLayerDefn()
        
        # For each feature in the input file create a buffer polygon in the new shapefile 
    for feature in inputlyr:
        #print feature
        
        ingeom = feature.GetGeometryRef()
        # if the feature has a geometry, buffer it
        if ingeom:
            geomBuffer = ingeom.Buffer(bufferDist)
            outFeature = ogr.Feature(featureDefn)
            outFeature.SetGeometry(geomBuffer)
            
            
            #copy fields
            for field in fieldlist:
                inputvalue= feature.GetField(field)
                outFeature.SetField(field, inputvalue)

            bufferlyr.CreateFeature(outFeature)

def main(inputfn, outputBufferfn, bufferDist):
    createBuffer(inputfn, outputBufferfn, bufferDist)
    
if __name__ == "__main__":
    inputfn = daShapefile
    outputBufferfn = output
    #set buffer size
    bufferDist = 500.0
    
    #run buffer
    main(inputfn, outputBufferfn, bufferDist)
    # copy projection
    proj = os.path.splitext(daShapefile)[0]+'.prj'
    outproj = os.path.splitext(output)[0]+'.prj'
    shutil.copy(proj, outproj)
    
