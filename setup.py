from setuptools import setup, find_packages


setup(
    name='edf2fif',
    py_modules=['edf2fif'],
    version='0.0.1',
    description='Converter fom edf to fif',
    long_description='Converter from edf to fif',
    url='https://github.com/uesseu',
    author='ninja',
    author_email='sheepwing@kyudai.jp',
    license='MIT',
    scripts=['bin/edf2fif.py'],
    requires=['mne', 'numpy', 'edflib'],
)
