import mne
import numpy as np
from tvbwidgets.ui.ts.data_wrappers.numpy_data_wrapper import WrapperNumpy

class WrapperEDF(WrapperNumpy):
    """Wraps EDF data for tswidget"""
    
    def __init__(self, filepath):
        # type: (str) -> None 
        
        self.raw = mne.io.read_raw_edf(filepath)
        data = self.raw.get_data()
        self.data = np.transpose(data)
        self.ch_idx = len(data.shape)-1
        self.sample_rate = self.raw.info['sfreq']
        super().__init__(self.data,self.sample_rate,ch_idx= self.ch_idx)
