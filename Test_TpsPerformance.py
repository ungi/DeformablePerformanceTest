

import cProfile, pstats, datetime
from io import BytesIO as StringIO
import math
import numpy
from os.path import expanduser, join


Scale = 100.0
WaveScale = 5.0
NumPerEdge = 5         # Number of TPS point pairs will be the cube of this number
NumExpFidsPerEdge = 3  # Number of experimental fiducials will be the cube of this number
ModelResolution = 200  # Higher number will create a more detailed model

Profiler = cProfile.Profile()
Profiler.enable()


# Create the FROM fiducial list, and hide it so it doesn't change with mouse interactions

fromFids = slicer.vtkMRMLMarkupsFiducialNode()
fromFids.SetName('FromFids')
slicer.mrmlScene.AddNode(fromFids)
for x in range(NumPerEdge):
  pos_x = (float(x) / (NumPerEdge - 1) - 0.5 )
  for y in range(NumPerEdge):
    pos_y = (float(y) / (NumPerEdge - 1) - 0.5 )
    for z in range(NumPerEdge):
      pos_z = (float(z) / (NumPerEdge - 1) - 0.5 )
      cx = pos_x * Scale
      cy = pos_y * Scale
      cz = pos_z * Scale
      fromFids.AddFiducial(cx, cy, cz)

fromFids.GetDisplayNode().SetVisibility(False)

# Create the TO fiducial list, and make its label text invisibly small

toFids = slicer.vtkMRMLMarkupsFiducialNode()
toFids.SetName('T')
slicer.mrmlScene.AddNode(toFids)
for x in range(NumPerEdge):
  pos_x = (float(x) / (NumPerEdge - 1) - 0.5 )
  for y in range(NumPerEdge):
    pos_y = (float(y) / (NumPerEdge - 1) - 0.5 )
    for z in range(NumPerEdge):
      pos_z = (float(z) / (NumPerEdge - 1) - 0.5 )
      cx = pos_x * Scale + math.sin(pos_y * math.pi * 2) * WaveScale
      cy = pos_y * Scale + math.cos(pos_z * math.pi) * WaveScale
      cz = pos_z * Scale
      toFids.AddFiducial(cx, cy, cz)

toFids.GetDisplayNode().SetTextScale(0)
toFids.GetDisplayNode().SetVisibility(True)

# Create the transform node to hold the deformable transformation later

tNode = slicer.vtkMRMLTransformNode()
tNode.SetName( 'TpsTransform' )
slicer.mrmlScene.AddNode( tNode )

tNode2 = slicer.vtkMRMLTransformNode()
tNode2.SetName( 'TpsTransform2' )
slicer.mrmlScene.AddNode( tNode2 )

tNode2.SetAndObserveTransformNodeID(tNode.GetID())

# Create a model to be transformed

SphereSource = vtk.vtkSphereSource()
SphereSource.SetRadius(Scale / 2.0)
SphereSource.SetThetaResolution(ModelResolution)
SphereSource.SetPhiResolution(ModelResolution)
SphereSource.Update()

ModelNode = slicer.vtkMRMLModelNode()
slicer.mrmlScene.AddNode( ModelNode )
ModelNode.SetName( "ModelNode" )
ModelNode.SetAndObservePolyData( SphereSource.GetOutput() )

DisplayNode = slicer.vtkMRMLModelDisplayNode()
slicer.mrmlScene.AddNode(DisplayNode)
ModelNode.SetAndObserveDisplayNodeID(DisplayNode.GetID())

ModelNode.SetAndObserveTransformNodeID(tNode2.GetID())


# Function that will be called whenever a TO fiducial moves and the transform needs an update

def updateTpsTransform(caller, eventid):
  numPerEdge = fromFids.GetNumberOfFiducials()
  if numPerEdge != toFids.GetNumberOfFiducials():
    print 'Error: Fiducial numbers are not equal!'
    return
  
  fp = vtk.vtkPoints()
  tp = vtk.vtkPoints()
  f = [0, 0, 0]
  t = [0, 0, 0]
  
  for i in range(numPerEdge):
    fromFids.GetNthFiducialPosition(i, f)
    toFids.GetNthFiducialPosition(i, t)
    fp.InsertNextPoint(f)
    tp.InsertNextPoint(t)
  
  tps = vtk.vtkThinPlateSplineTransform()
  tps.SetSourceLandmarks( fp )
  tps.SetTargetLandmarks( tp )
  tps.SetBasisToR()
  
  tps2 = vtk.vtkThinPlateSplineTransform()
  tps2.SetSourceLandmarks( tp )
  tps2.SetTargetLandmarks( fp )
  tps.SetBasisToR()
  
  tNode.SetAndObserveTransformToParent( tps )
  tNode2.SetAndObserveTransformToParent( tps2 )


toFids.AddObserver(vtk.vtkCommand.ModifiedEvent, updateTpsTransform)

# A ROI annotation defines the region where the transform will be visualized

roi = slicer.vtkMRMLAnnotationROINode()
roi.SetName( 'RoiNode' )
slicer.mrmlScene.AddNode( roi )
roi.SetDisplayVisibility(False)
roi.SetXYZ(0, 0, 0)
roi.SetRadiusXYZ(Scale / 2.0, Scale / 2.0, Scale / 2.0)

updateTpsTransform(None, None)

# Create new fiducial list and transform fiducials using the deformation

expFids = slicer.vtkMRMLMarkupsFiducialNode()
expFids.SetName('E')
slicer.mrmlScene.AddNode(expFids)
for x in range(NumExpFidsPerEdge):
  pos_x = (float(x) / (NumExpFidsPerEdge - 1) - 0.5 )
  for y in range(NumExpFidsPerEdge):
    pos_y = (float(y) / (NumExpFidsPerEdge - 1) - 0.5 )
    for z in range(NumExpFidsPerEdge):
      pos_z = (float(z) / (NumExpFidsPerEdge - 1) - 0.5 )
      cx = pos_x * Scale
      cy = pos_y * Scale
      cz = pos_z * Scale
      expFids.AddFiducial(cx, cy, cz)

expFids.SetAndObserveTransformNodeID(tNode.GetID())
expFids.GetDisplayNode().SetVisibility(True)
expFids.GetDisplayNode().SetTextScale(0)
expFids.GetDisplayNode().SetSelectedColor(1,1,0)

numExpFids = expFids.GetNumberOfFiducials()
for i in range(numExpFids):
  p = numpy.zeros(4)
  expFids.GetNthFiducialWorldCoordinates(i, p)

updateTpsTransform(None, None)

Profiler.disable()
StatsString = StringIO()
SortBy = u'name'
ProfileStats = pstats.Stats(Profiler, stream=StatsString).sort_stats(SortBy)
ProfileStats.print_stats()
out = StatsString.getvalue()
print(out)

home = expanduser("~")
FileName = join( home, "TpsTest_{0}.txt".format(str(datetime.datetime.now())).replace(':', '_') )


with open(FileName, 'w') as outfile:
  outfile.write(out)
