# demodulate-search
Scripts for computing de-orbited time series from filterbank data and searching for a second pulsar in the companion of a binary pulsar. It has been written to search for the companion of PSR J1208-5936. It uses a fork of https://github.com/alex88ridolfi/pysolator.6. Both ```deOrbitFFA.py``` and ```deOrbitFFT.py``` clean a filterbank file with ```rfifind```, dedisperse it with ```prepdata``` and de-modulate the pulsar's orbit at several mass ratio trials with ```pysolator.bin``` (from https://github.com/alex88ridolfi/pysolator.6). Both scripts need an input list of inclination angle trials to work, as it is assumed that the user does not know the mass ratio a priory. Thereafter, ```deOrbitFFA.py``` applies riptide (https://github.com/v-morello/riptide) to search and fold candidates, while ```deOrbitFFT.py``` uses a combination of ```realfft```, ```rednoise```, ```accelsearch``` and ```prepfold```. More info on their usage with ```-h```.

Both ```deOrbitFFA.py``` and ```deOrbitFFT.py``` are written in a segmented way. Therefore, they recognize if de-modulated time series are already available before calling ```pysolator.bin``` or if search reasuls are already available and therefore it is possible to go straight to folding. 

The scripts have been written in singularity-based environment. However, they can be easily modified to adjust for your own environment by editing the python subprocess commands. Running them requires python3, numpy, presto (https://github.com/scottransom/presto) and riptide (https://github.com/v-morello/riptide) if using ```deOrbitFFA.py```.

To use both ```deOrbitFFA.py``` and ```deOrbitFFT.py```, if ```pysolator.bin``` is called, scipy is also needed in addition to numpy. 

# Questions and suggestions.

Contact mcbernadich@mpifr-bonn.mpg.de if you have any.
