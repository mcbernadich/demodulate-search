# demodulateSearch
Scripts for computing de-orbited time series from filterbank data and searching for a second pulsar in the companion of a binary pulsar. It has been written to search for the companion of PSR J1208-5936. It uses a fork of https://github.com/alex88ridolfi/pysolator.6

The scripts have been writen to use a singularity-based environment. However, they can be easily modified to adjust for your own environment by changing the sybprocess commands. Running them requires python3, numpy, presto (https://github.com/scottransom/presto) and riptide (https://github.com/v-morello/riptide) if using the FFA version.
