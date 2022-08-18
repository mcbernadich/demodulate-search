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

parser=argparse.ArgumentParser(description="Demodulate a binary pulsar with pysolator.bin, and search it with presto.")
parser.add_argument("--path",help="Path towards the filterbanks.")
parser.add_argument("--inclinations",help="File with rows of {i, sin(i), M2}. Each row is a demodulation.")
parser.add_argument("--parameter",help="DDGR parameter file with MTOT, M2 and SINI.")
parser.add_argument("--dm",help="Dedispersion DM value.")
parser.add_argument("--out",help="Root name of the created files. If '--path' is not given, it will look for a time series with this root.")
parser.add_argument("--nharm",help="Number of harmonics to sum. Default: 16")
parser.add_argument("--zmax",help="Frequency derivative range for accelssearch. Default: 0. s-1/s")
parser.add_argument("--max_cands",type=int,help="Number of candidates to fold. Default: 16")
args = parser.parse_args()

out=args.out
if args.nharm:
	nharm=str(int(args.nharm))
else:
	nharm="16"

if args.zmax:
	zmax=str(int(args.zmax))
else:
	zmax="0"

if args.max_cands:
	max_cands=args.max_cands
else:
	max_cands=16

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
fourier_transforms=glob.glob("datFiles/*_red.fft")

if len(fourier_transforms)==0:

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

		#Perform a fourier transform here, and de-redden.
		time_series=glob.glob("*_0of1_q*.dat")
		sub.run(["singularity","exec","-B","/:/data:ro","/beegfs/u/ebarr/singularity_images/fold-tools-2020-11-18-4cca94447feb.simg","realfft",time_series[0]])
		fourier_transform=glob.glob("*_0of1_q*.fft")
		sub.run(["singularity","exec","-B","/:/data:ro","/beegfs/u/ebarr/singularity_images/fold-tools-2020-11-18-4cca94447feb.simg","rednoise",fourier_transform[0]])

		mv_Files=glob.glob("*_0of1_q*")
		for file in mv_Files:
			sub.run(["mv",file,"datFiles"])

		mv_Files=glob.glob("isol*")
		for file in mv_Files:
			sub.run(["mv",file,"datFiles"])

		i=i+1

else:

	print("")
	print("Demodulated Fourier transforms are already found in the './datFiles' directory. If you want to re-compute them, move the old ones somewhere else.")
	print("")


#Fourer-searching part of the series.
print(" ")
print("Working on the following Fourier series:")
print(" ")
fourier_transforms=glob.glob("datFiles/*_red.fft")
candidate_files=[file.split(".")[0]+"."+file.split(".")[1]+"_ACCEL_"+str(int(2*(int(zmax)+1)/2))+".cand" for file in fourier_transforms]
candidate_files_test=glob.glob("datFiles/*ACCEL*")
n_gulp=4
i=0
i_max=len(fourier_transforms)

if len(candidate_files_test)==0:

	while i < i_max:
		print(fourier_transforms[i:i+n_gulp])
		search_commands = [["singularity","exec","-B","/:/data:ro","/beegfs/u/ebarr/singularity_images/fold-tools-2020-11-18-4cca94447feb.simg","accelsearch","-zmax",zmax,"-ncpus","4","-numharm",nharm,file] for file in fourier_transforms[i:i+n_gulp]]
		search_processes = [sub.Popen(command, stdout=sub.DEVNULL) for command in search_commands]
		for process in search_processes:
			process.wait()
		print("Folding candidates")
		print(" ")		
		for j in range(1,max_cands+1):
			fold_commands = [["singularity","exec","-B","/:/data:ro","/beegfs/u/ebarr/singularity_images/fold-tools-2020-11-18-4cca94447feb.simg","prepfold","-ncpus","4","-nosearch","-accelcand",str(j),"-accelfile",cand_file,data_file.split("_red.")[0]+".dat"] for (cand_file,data_file) in zip(candidate_files[i:i+n_gulp],fourier_transforms[i:i+n_gulp])]
			fold_processes= [sub.Popen(command, stdout=sub.DEVNULL, stderr=sub.DEVNULL) for command in fold_commands]
			for process in fold_processes:
				process.wait()
		mv_Files=glob.glob("datFiles/*pfd*")
		for file in mv_Files:
			sub.run(["mv",file,"candidatePlots"])
		i=i+n_gulp

else:
	print("")
	print("Search results are already found in the './datFiles' directory. If you want to re-compute them, move the old ones somewhere else.")
	print("")