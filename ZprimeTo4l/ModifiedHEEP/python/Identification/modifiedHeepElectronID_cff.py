import FWCore.ParameterSet.Config as cms

from RecoEgamma.ElectronIdentification.Identification.heepElectronID_tools import HEEP_WorkingPoint_V1
from ZprimeTo4l.ModifiedHEEP.Identification.modifiedHeepElectronID_tools import configureModifiedHEEPElectronID
from RecoEgamma.ElectronIdentification.Identification.heepElectronID_HEEPV70_cff import WP_HEEP70_EB,WP_HEEP70_EE
import copy

idName = "modifiedHeepElectronID"
WP_modHEEP_EB = copy.deepcopy(WP_HEEP70_EB)
WP_modHEEP_EB.idName = str(idName)
WP_modHEEP_EE = copy.deepcopy(WP_HEEP70_EE)
WP_modHEEP_EE.idName = str(idName)

modifiedHeepElectronID = configureModifiedHEEPElectronID(idName, WP_modHEEP_EB, WP_modHEEP_EE)
modifiedHeepElectronID.isPOGApproved = cms.untracked.bool(False)
