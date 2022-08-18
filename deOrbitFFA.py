#!/usr/bin/env python3
#################### Miquel Colom i Bernadich, 18/08/2022 ########################

import numpy as np
import subprocess as sub
from os.path import exists
import glob
import argparse
import sys

def change_inclination(parFile,M2,SINI,sufix):

	par_read=open(parFile,"r")
	parFile_new=parFile.split(".")[0]+"_"+str(sufix)+".par"
	par_write=open(parFile_new,"w")
	for line in par_read:
		chunks = line.strip().split()
		if chunks[0]=="M2":
			par_write.write("M2 "+str(M2)+"\n")
		elif chunks[0]=="SINI":
			par_write.write("SINI "+str(SINI)+"\n")
		else:
			par_write.write(line)

	par_read.close()
	par_write.close()

	return parFile_new

# Read the periods of candidates of the riptide logs.
def read_candidates_from_logs(riptidelogs,name,p_range):
	candidates_file=name.split(".dat")[0]+"_"+p_range+"_FFA-SEARCH_candidates.txt"
	write_file=open(candidates_file,"w")
	periods=[]
	logs=riptidelogs.split("[")[1].split("]")[0].strip()
	write_file.write("period,freq,width,ducy,snr\n")
	for line in logs.split("Peak(")[1:]:
		line=line.split(", dm=None")[0].split(",")
		period=str(float(line[0].split("=")[1]))
		periods.append(period)
		freq=str(float(line[1].split("=")[1]))
		width=str(float(line[2].split("=")[1]))
		ducy=str(float(line[3].split("=")[1]))
		snr=str(float(line[6].split("=")[1]))
		write_file.write(period+","+freq+","+width+","+ducy+","+snr+"\n")
	write_file.close()
	return periods

def repair_inf_file(original_file):

	read_file=open(original_file,"r")
	write_file=open(original_file.split(".inf")[0]+"_new.inf","w")
	for line in read_file:
		if "_red" in line:
			write_file.write(line.split("_red")[0]+"\n")
		else:
			write_file.write(line)

	return original_file.split(".inf")[0]+"_new.inf"

parser=argparse.ArgumentParser(description="Demodulate a binary pulsar with pysolator.bin, and search it with riptide.")
parser.add_argument("--path",help="Path towards the filterbanks.")
parser.add_argument("--inclinations",help="File with rows of {i, sin(i), M2}. Each row is a demodulation.")
parser.add_argument("--parameter",help="DDGR parameter file with MTOT, M2 and SINI.")
parser.add_argument("--dm",help="Dedispersion DM value.")
parser.add_argument("--out",help="Root name of the created files. If '--path' is not given, it will look for a time series with this root.")
parser.add_argument("--conf",help="Path to configuration file.")
args = parser.parse_args()

out=args.out

if args.path:

	filterbanks_path=args.path
	dm=args.dm

	files=sorted(glob.glob(filterbanks_path+"*.fil"))

	print("")
	print("Creating a mask for the time series.")
	print("")
	command=["singularity","exec","-B","/:/data:ro","/beegfs/u/ebarr/singularity_images/fold-tools-2020-11-18-4cca94447feb.simg","rfifind","-ncpus","8","-o",out]
	for file in files:
		command.append("/data"+file)
	sub.run(command)

	print("")
	print("Creating the time series.")
	print("")
	command=["singularity","exec","-B","/:/data:ro","/beegfs/u/ebarr/singularity_images/fold-tools-2020-11-18-4cca94447feb.simg","prepdata","-ncpus","8","-dm",dm,"-mask",out+"_rfifind.mask","-o",out]
	for file in files:
		command.append("/data"+file)
	sub.run(command)

sub.run(["mkdir","parFiles"])
sub.run(["mkdir","datFiles"])
sub.run(["mkdir","candidatePlots"])


#De-orbiting and making time series part.
i=0
time_series=glob.glob("datFiles/*_0of1_q*.dat")

if len(time_series)==0:

	#parFile="J1208-5936_20220111_DDGR.par"
	parFile=args.parameter
	inclinations_list=args.inclinations
	incls=np.loadtxt(inclinations_list,delimiter=", ")

	for row in incls:

		SINI=row[1]
		M2=row[2]
		parFile_new=change_inclination(parFile,M2,SINI,SINI)
		print(parFile_new)

		sub.run(["singularity","exec","-B","/:/data:ro","/beegfs/u/mcbernadich/simages/pyfitorbit.sif","python3","pysolator.bin","-par",parFile_new,"-datfile",out+".dat","-ncpus","16"])

#		if i/10==int(i/10):
#			par=glob.glob("*noorb.par")[0]
#			dat=glob.glob("isol*_p.dat")[0]	
#			sub.run(["singularity","exec","-B","/:/data:ro","/beegfs/u/ebarr/singularity_images/fold-tools-2020-11-18-4cca94447feb.simg","prepfold","-par",par,dat])

		sub.run(["mv",parFile_new,"parFiles"])

		mv_Files=glob.glob("*comp.par")
		for file in mv_Files:
			sub.run(["mv",file,"parFiles"])

		mv_Files=glob.glob("*noorb.par")
		for file in mv_Files:
			sub.run(["mv",file,"parFiles"])

		mv_Files=glob.glob("*_0of1_q*")
		for file in mv_Files:
			sub.run(["mv",file,"datFiles"])

		mv_Files=glob.glob("isol*")
		for file in mv_Files:
			sub.run(["mv",file,"datFiles"])

		i=i+1

else:

	print("")
	print("Demodulated time series are already found in the './datFiles' directory. If you want to re-compute them, move the old ones somewhere else.")
	print("")

info_file=open(out+".inf","r")
for line in info_file:
	if "Width of each time series bin (sec)" in line:
		time_sampling=str(float(line.split("=")[1]))
info_file.close()

#Searching the series.
print(" ")
print("Working on the following time series:")
print(" ")
time_series_inf=sorted(glob.glob("datFiles/*_0of1_q*c.inf"))
n_gulp=2
i=0
i_max=len(time_series)

while i < i_max:
	print(time_series[i])
	folder="candidatePlots/"+time_series_inf[i].split(".inf")[0].split("/")[1]
	sub.run(["mkdir",folder])
	sub.run(["cp",time_series_inf[i].split(".inf")[0]+"_red.inf",time_series_inf[i]],stdout=sub.DEVNULL)
	repaired_file=repair_inf_file(time_series_inf[i])
	sub.run(["mv",repaired_file,time_series_inf[i]],stdout=sub.DEVNULL)
	sub.run(["singularity","exec","-B","/:/data:ro","/beegfs/u/mcbernadich/simages/riptide-ffa_latest-2021-03-29-c43894cdf84c.simg","rffa","-c",args.conf,"-o",folder,time_series_inf[i]],stdout=sub.DEVNULL)
	i=i+1
