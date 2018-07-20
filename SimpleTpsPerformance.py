

import cProfile, pstats, datetime
from io import BytesIO as StringIO
import math
import numpy
from os.path import expanduser, join


Scale = 100.0
WaveScale = 5.0
NumPerEdge = 5         # Number of TPS point pairs will be the cube of this number
ModelResolution = 200  # Higher number will create a more detailed model

Profiler = cProfile.Profile()
Profiler.enable()


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


tps = vtk.vtkThinPlateSplineTransform()
tps.SetSourceLandmarks( FromPoints )
tps.SetTargetLandmarks( ToPoints )
tps.SetBasisToR()

tps2 = vtk.vtkThinPlateSplineTransform()
tps2.SetSourceLandmarks( FromPoints )
tps2.SetTargetLandmarks( ToPoints )
tps.SetBasisToR()

tNode.SetAndObserveTransformToParent( tps )
tNode2.SetAndObserveTransformToParent( tps2 )


Profiler.disable()
StatsString = StringIO()
SortBy = u'cumtime'
ProfileStats = pstats.Stats(Profiler, stream=StatsString).sort_stats(SortBy)
ProfileStats.print_stats()
out = StatsString.getvalue()
print(out)

home = expanduser("~")
FileName = join( home, "TpsTest_{0}.txt".format(str(datetime.datetime.now())).replace(':', '_') )


with open(FileName, 'w') as outfile:
  outfile.write(out)
