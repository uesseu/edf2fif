# EDF2FIF
A python script to translate edf file(brain wave) to
fif file(MNEpython/MEG/elekta).

# dependency
This module requires python and these packages.

- numpy
- mne
- pyedflib

python2 and 3 are supported ;)

# Install
'''bash
pip install numpy mne pyedflib
pip install git+https://github.com/uesseu/edf2fif
'''

# usage
You can use it as command line tool and python module.

## From Shell

```bash
edf2fif -i input -o output -s settingfile
```

If you want help,
```
edf2fif -h
```

## From python

```python
setting_file = 'setting.json'
e2f = EDF2FIF()
e2f.load_setting(setting_file)
e2f.load_eeg(edf_file)
e2f.make_mne_raw()
e2f.save_fif(outfile)
```

## Setting file
It needs a setting file because edf files has event list,
which can be set by users.
Event list of fif is numeric, and fif file cannot contain
event list as strings. :(

Setting file is a json file. But not so long.
(I want to write it in toml some day...)

event: dict of events  { edf : fif }
channel_list: channels { edf : fif } 
type: types. eeg, eog, meg, ecg, stim, misc and so on.
    If you want to know details, read MNE python's API.
reference: reference of eeg. If None, averaged reference.
    If multiple channels were selected, mean of them are used.
exclude: List of channels to drop.
montage: name of montage.
    If you want to know details, read MNE python's API.

## Example of Setting file
See settings.json ;)

## Touble Shooting
If you want to EDF+D fomat, you have to convert it to
EDF+C fomat.
For example, EDFbrowser can convert it.
