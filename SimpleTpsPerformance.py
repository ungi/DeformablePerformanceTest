

import cProfile, pstats, datetime
from io import BytesIO as StringIO
import math
import numpy
from os.path import expanduser, join

# Parameters to control test size

Scale = 100.0
WaveScale = 5.0
NumPerEdge = 6         # Number of TPS point pairs will be the cube of this number
ModelResolution = 200  # Higher number will create a more detailed model

# Start profiler

Profiler = cProfile.Profile()
Profiler.enable()

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

# Create deformable transform

FromPoints = vtk.vtkPoints()
ToPoints = vtk.vtkPoints()

for x in range(NumPerEdge):
  pos_x = (float(x) / (NumPerEdge - 1) - 0.5 )
  for y in range(NumPerEdge):
    pos_y = (float(y) / (NumPerEdge - 1) - 0.5 )
    for z in range(NumPerEdge):
      pos_z = (float(z) / (NumPerEdge - 1) - 0.5 )
      cx = pos_x * Scale
      cy = pos_y * Scale
      cz = pos_z * Scale
      FromPoints.InsertNextPoint(cx, cy, cz)
      cx = pos_x * Scale + math.sin(pos_y * math.pi * 2) * WaveScale
      cy = pos_y * Scale + math.cos(pos_z * math.pi) * WaveScale
      cz = pos_z * Scale
      ToPoints.InsertNextPoint(cx, cy, cz)

tNode = slicer.vtkMRMLTransformNode()
tNode.SetName( 'TpsTransform' )
slicer.mrmlScene.AddNode( tNode )

tps = vtk.vtkThinPlateSplineTransform()
tps.SetSourceLandmarks( FromPoints )
tps.SetTargetLandmarks( ToPoints )
tps.SetBasisToR()

# Apply deformable transform on model

tNode.SetAndObserveTransformToParent( tps )
ModelNode.SetAndObserveTransformNodeID(tNode.GetID())

# Print profiler output

Profiler.disable()
StatsString = StringIO()
SortBy = u'name'
ProfileStats = pstats.Stats(Profiler, stream=StatsString).sort_stats(SortBy)
ProfileStats.print_stats()
out = StatsString.getvalue()
print(out)

home = expanduser("~")
FileName = "TpsTest_{0}_Slicer-{1}.{2}.txt".format(
  str(datetime.datetime.now()), slicer.app.majorVersion, slicer.app.minorVersion).replace(':', '_')
FilePathName = join(home, FileName)

with open(FilePathName, 'w') as outfile:
  outfile.write(out)

