from shapely.geometry import Point, mapping, shape
from fiona import collection
import shapely.ops
from shapely.ops import unary_union, polygonize #not sure its necessary to import these again if I'm importing shapely.ops as a whole

input_buffer = r"C:\GIS\data\trailbuffer500.zip" #this is the output from Matt's buffer script at 500m distance
output_buffer = r"C:\GIS\data\overlaps500.shp" #output will be a shapefile showing only the areas in the input where two trail buffers overlap

with fiona.open(input_buffer) as layer:
    rings = [LineString(list(shape(pol['geometry']).exterior.coords)) for pol in layer] #converts the buffer polygons to polylines, to compare their perimter locations
    
    union = unary_union(rings) #finds the areas where ring perimeters cross
    result = [geom for geom in polygonize(union)] #encodes the coordinates for perimeter back inyo polygon geometry
    schema=layer.schema.copy() #captures the attribute table style from the input to carry over to output
    schema['properties']['area'] = 'float:10.2' #unsure what this is doing but didn't want to remove it unless it causes an error
    with fiona.open(output_buffer, 'w', 'ESRI Shapefile', schema) as c: #creates output shapefile
        for index, pol in enumerate(result): #loops through individual features in the file, since it's a single file containign multiple polygons
            c.write({'geometry': mapping(pol),'properties': {'id': index, 'area': pol.area}}) #writes attributes to shapefile, inckluding geomtry, object id, and the shape area
