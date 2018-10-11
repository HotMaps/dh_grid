import numpy as np
import os
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import sys
from scipy.ndimage import measurements
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)
from CM.CM_TUW1.read_raster import raster_array as RA


def add_label_field(heat_dem_coh_last, heat_dem_spec_area, q, q_spec_cost,
                    economic_bool, area_coh_area, out_raster_coh_area_bool,
                    out_raster_labels, out_shp_prelabel, out_shp_label,
                    epsg=3035):
    label_list = []
    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    # Remove output shapefile if it already exists
    if os.path.exists(out_shp_label):
        outDriver.DeleteDataSource(out_shp_label)
    bool_arr, gt = RA(out_raster_coh_area_bool, return_gt=True)
    label_arr = RA(out_raster_labels)
    numLabels = np.max(label_arr)
    coords = measurements.center_of_mass(bool_arr, label_arr,
                                         index=np.arange(1, numLabels+1))
    x0, y0, w, h = gt[0], gt[3], gt[1], gt[5]
    X0 = x0 + w/2
    Y0 = y0 + h/2
    for item in coords:
        xl = round(X0 + 100 * item[1], 1)
        yl = round(Y0 - 100 * item[0], 1)
        label_list.append((xl, yl))
    inDriver = ogr.GetDriverByName("ESRI Shapefile")
    inDataSource = inDriver.Open(out_shp_prelabel, 0)
    inLayer = inDataSource.GetLayer()
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    geom_typ = inLayer.GetGeomType()
    geom_typ_dict = {1: ogr.wkbPoint, 2: ogr.wkbLineString, 3: ogr.wkbPolygon}
    # Create the output Layer
    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    outDataSource = outDriver.CreateDataSource(out_shp_label)
    outLayer = outDataSource.CreateLayer("newSHP", srs,
                                         geom_type=geom_typ_dict[geom_typ])
    Fields = ['label', 'economic', 'heat_dem_l', 'sp_h_d', 'pot_dh_dem',
              'dist_cost', 'area[ha]']
    Fields_dtype = [ogr.OFTInteger, ogr.OFTInteger, ogr.OFTReal, ogr.OFTReal,
                    ogr.OFTReal, ogr.OFTReal, ogr.OFTReal]
    for i, f in enumerate(Fields):
        Field = ogr.FieldDefn(f, Fields_dtype[i])
        outLayer.CreateField(Field)
    # Get the output Layer's Feature Definition
    outLayerDefn = outLayer.GetLayerDefn()
    for feature in inLayer:
        geom = feature.GetGeometryRef()
        centroid = geom.Centroid()
        x = round(centroid.GetX(), 1)
        y = round(centroid.GetY(), 1)
        outFeature = ogr.Feature(outLayerDefn)
        try:
            geom_label = label_list.index((x, y))
        except:
            nearest_dist = 1000
            for p, point in enumerate(label_list):
                x_temp, y_temp = point
                temp_dist = ((x-x_temp)**2 + (y-y_temp)**2)**0.5
                if temp_dist < nearest_dist:
                    geom_label = p
        outFeature.SetField(outLayerDefn.GetFieldDefn(0).GetNameRef(),
                            geom_label+1)
        outFeature.SetField(outLayerDefn.GetFieldDefn(1).GetNameRef(),
                            economic_bool[geom_label])
        outFeature.SetField(outLayerDefn.GetFieldDefn(2).GetNameRef(),
                            heat_dem_coh_last[geom_label])
        outFeature.SetField(outLayerDefn.GetFieldDefn(3).GetNameRef(),
                            heat_dem_spec_area[geom_label])
        outFeature.SetField(outLayerDefn.GetFieldDefn(4).GetNameRef(),
                            q[geom_label])
        outFeature.SetField(outLayerDefn.GetFieldDefn(5).GetNameRef(),
                            q_spec_cost[geom_label])
        outFeature.SetField(outLayerDefn.GetFieldDefn(6).GetNameRef(),
                            area_coh_area[geom_label])
        outFeature.SetGeometry(geom)
        # Add new feature to output Layer
        outLayer.CreateFeature(outFeature)
        outFeature = None
    # Save and close DataSources
    inDataSource = None
    outDataSource = None
    if os.path.exists(out_shp_prelabel):
        outDriver.DeleteDataSource(out_shp_prelabel)


def polygonize(heat_dem_coh_last, heat_dem_spec_area, q, q_spec_cost,
               economic_bool, area_coh_area, out_raster_coh_area_bool,
               out_raster_labels, out_shp_prelabel, out_shp_label, epsg=3035):
    # save the coherent areas in shapefile format
    raster = gdal.Open(out_raster_coh_area_bool)
    band = raster.GetRasterBand(1)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    shpDriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(out_shp_prelabel):
        shpDriver.DeleteDataSource(out_shp_prelabel)
    outDataSource = shpDriver.CreateDataSource(out_shp_prelabel)
    outLayer = outDataSource.CreateLayer('outPrePolygon', srs,
                                         geom_type=ogr.wkbPolygon)
    newField = ogr.FieldDefn('Feature', ogr.OFTInteger)
    outLayer.CreateField(newField)
    # polygonize
    gdal.Polygonize(band, band, outLayer, 0, options=["8CONNECTED=8"])
    # save layer
    outDataSource = outLayer = band = None
    add_label_field(heat_dem_coh_last, heat_dem_spec_area, q, q_spec_cost,
               economic_bool, area_coh_area, out_raster_coh_area_bool,
               out_raster_labels, out_shp_prelabel, out_shp_label)
