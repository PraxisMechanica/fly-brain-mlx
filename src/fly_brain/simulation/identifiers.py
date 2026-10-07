from typing import NewType

import numpy as np
from numpy.typing import NDArray

FlyWireNeuronId = NewType('FlyWireNeuronId', int)
NeuronRow = NewType('NeuronRow', int)
TrialId = NewType('TrialId', int)

FlyWireIds64 = NewType('FlyWireIds64', NDArray[np.int64])
NeuronRows32 = NewType('NeuronRows32', NDArray[np.int32])
NeuronRows64 = NewType('NeuronRows64', NDArray[np.int64])
EdgeRows32 = NewType('EdgeRows32', NDArray[np.int32])
PaddedEdgeRows32 = NewType('PaddedEdgeRows32', NDArray[np.int32])
TrialIds16 = NewType('TrialIds16', NDArray[np.int16])
TrialIds64 = NewType('TrialIds64', NDArray[np.int64])
