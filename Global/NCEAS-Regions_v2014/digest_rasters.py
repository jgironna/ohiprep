# cmd: C:\Python27\ArcGISx6410.2\python.exe G:\ohiprep\Global\NCEAS-Regions_v2014\digest_rasters.py

# convert feature classes to rasters
import arcpy, os, subprocess, csv, sys, socket, time
from arcpy.sa import *

# configuration based on machine name
dirs = {
    'amphitrite':
    {'git'    :'G:/ohiprep',
     'neptune':'N:',
     'tmp'    :'C:/tmp',
     },
    'optimus':
    {'git'    :'D:/best/docs/GitHub/ohiprep',
     'neptune':'N:',
     'tmp'    :'D:/best/tmp',
     }}[socket.gethostname().lower()]

# paths
prod     = 'Global/NCEAS-Regions_v2014'                # name of product
dir_git  = '%s/%s' % (dirs['git'], prod)               # github directory inside ohiprep
dir_tmp  = '%s/%s' % (dirs['tmp'], prod)               # temp directory on local filesystem
dir_anx  = '%s/git-annex/%s' % (dirs['neptune'], prod) # git annex directory on neptune
gdb      = '%s/geodb.gdb' % dir_tmp                    # file geodatabase
mask     = '%s/model/GL-NCEAS-Halpern2008/data/masked_model.tif' % dirs['neptune']

# projections
sr_mol = arcpy.SpatialReference('Mollweide (world)') # projected Mollweide (54009)
sr_gcs = arcpy.SpatialReference('WGS 1984')          # geographic coordinate system WGS84 (4326)

# shapefiles don't have nulls, so use geodatabase
if not os.path.exists(dir_tmp):
    os.makedirs(dir_tmp)
if not os.path.exists(dir_anx):
    os.makedirs(dir_anx)
if not arcpy.Exists(gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(gdb), os.path.basename(gdb))

# workspace & scratch space
arcpy.CheckOutExtension('Spatial')
os.chdir(dir_tmp)
arcpy.env.workspace              = gdb
arcpy.env.scratchWorkspace       = dir_tmp
arcpy.env.outputCoordinateSystem = None # arcpy.SpatialReference('Mollweide (world)')
arcpy.env.overwriteOutput        = 1

# copy mask
print('copying mask to local tmp: %s' % mask)
m = '%s/%s' % (dir_tmp, os.path.basename(mask))
#arcpy.Copy_management(mask, m) # arcpy.Exists(m)

# set
cellsize = arcpy.GetRasterProperties_management(m,'CELLSIZEX') # 934.478877011219

# TODO: copy over needed features if not present in tmp/gdb
buffers = ['offshore','inland','inland1km','offshore1km','offshore3nm','inland25km','inland50km']
for buf in buffers:          # buf = buffers[0]
    for pfx in ('rgn', 'sp'): # pfx = ('sp','rgn')[0]

        # debug: buf = 'offshore'; pfx = 'rgn'
        print('%s_%s' % (pfx, buf))

        fc_gcs  = '%s/%s_%s_gcs' % (gdb, pfx, buf)
        fc_mol  = '%s/%s_%s_mol' % (gdb, pfx, buf)        
        tif_mol = '%s/data/%s_%s_mol.tif' % (dir_tmp, pfx, buf)
        tif_gcs = '%s/data/%s_%s_gcs.tif' % (dir_tmp, pfx, buf)
        fld_id  = '%s_id' % pfx

        # project feature class to Mollweide
        #print('  *_mol.shp (%s)' % time.strftime('%H:%M:%S'))
        #arcpy.Project_management(fc_gcs, fc_mol, sr_mol)

        # project to raster, setting snap raster first to sp_[mol|gcs].tif
        print('  *_mol.tif (%s)' % time.strftime('%H:%M:%S'))
        arcpy.env.outputCoordinateSystem = m
        arcpy.env.snapRaster = m
        arcpy.env.extent = m
        arcpy.FeatureToRaster_conversion(fc_mol, fld_id, tif_mol, cellsize) # meters
        
        print('  *_gcs.tif (%s)' % time.strftime('%H:%M:%S'))
        arcpy.env.outputCoordinateSystem = sr_gcs
        arcpy.env.extent = None
        if (pfx, buf) != ('sp','offshore'):
            arcpy.env.snapRaster = '%s/data/sp_offshore_gcs.tif' % dir_tmp
        else:
            arcpy.env.snapRaster = None
        arcpy.FeatureToRaster_conversion(fc_gcs, fld_id, tif_gcs,  0.1) # degrees

        # copy to server
        print('  copying to server (%s)' % time.strftime('%H:%M:%S'))
        #arcpy.CopyFeatures_management( fc_mol, '%s/data/%s_%s_mol.shp' % (dir_anx, pfx, buf))
        arcpy.Copy_management(        tif_mol, '%s/data/%s_%s_mol.tif' % (dir_anx, pfx, buf))
        arcpy.Copy_management(        tif_gcs, '%s/data/%s_%s_gcs.tif' % (dir_anx, pfx, buf))