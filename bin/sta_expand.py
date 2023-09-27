#!/usr/bin/env python3

from IsoNet.bin.sta_peet import sta_peet_one
from IsoNet.objects.expand import Expand
import sys,os
import subprocess
import imodmodel
import logging
import numpy as np
from IsoNet.util.star_metadata import MetaData
from IsoNet.objects.tomogram import Tomogram
from IsoNet.util.utils import mkfolder
from IsoNet.util.searchParam import SearchParam

star_file = sys.argv[1]
param_file = sys.argv[2]
tomoName = sys.argv[3]
max_exp_num = int(sys.argv[4])
min_patch_size = int(sys.argv[5])
cpus = int(sys.argv[6])


#max_exp_num = 6

md = MetaData()
md.read(star_file)
#md.printStar()
item = None
for i in md:
    if i.rlnTomoName == tomoName:
        item = i
        break
#######  create Folder, prepare *prm* file, mrc/rec , mod, rotaxes.csv , motl.csv  ###########
if item != None:
    tomo = Tomogram(item.rlnTomoName, initialParamFolder=item.rlnInitialParamFolder, \
    reconstructionPath=item.rlnReconstructionPath, pickingPath=item.rlnPickingPath)
else:
    sys.exit()
if max_exp_num == 0:
    cache_folder_path = "{}_cache".format(tomo.staPath)
    latest_round = -1

    if os.path.exists(cache_folder_path):
      cache_folder_list = []
      for dir in os.listdir(cache_folder_path):
          if dir.startswith("round"):
              cache_folder_list.append(dir)
      rounds_num = [int(x.split("_")[1]) for x in cache_folder_list]
      if len(rounds_num) > 0:
        latest_round = max(rounds_num)
      latest_cache_folder_path = "{}_cache/round_{}".format(tomo.staPath,latest_round)

      if not os.path.exists("{}/exp/{}_exp.mod".format(latest_cache_folder_path, tomo.tomoName)):
        cmd = "rm {}/* -rf".format(cache_folder_path) 
        subprocess.check_output(cmd, shell=True)
        latest_round = -1
        tomo.setInitialParams()
        
      else:
        tomo.updateAlignmentFile(latest_round, latest_cache_folder_path)
    else:
      tomo.setInitialParams()
    
    tomo.setReconstructionPath()
    tomo.getParticleNumber()
    tomo.setTilt()
else:
    cache_folder_path = "{}_cache".format(tomo.staPath)
    latest_round = -1

    if os.path.exists(cache_folder_path):
      cache_folder_list = []
      for dir in os.listdir(cache_folder_path):
          if dir.startswith("round"):
              cache_folder_list.append(dir)
      rounds_num = [int(x.split("_")[1]) for x in cache_folder_list]
      if len(rounds_num) > 0:
        latest_round = max(rounds_num)
      latest_cache_folder_path = "{}_cache/round_{}".format(tomo.staPath,latest_round)

      if not os.path.exists("{}/exp/{}_exp.mod".format(latest_cache_folder_path, tomo.tomoName)):
        latest_round = -1

########################
log_file = "Expand/expand.log"

logger = logging.getLogger(__name__)
handler = logging.FileHandler(filename=log_file, mode='a')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
formatter.datefmt = "%y-%m-%d %H:%M:%S"
logger.handlers = [handler]
logger.setLevel(logging.INFO)
########################


for i in range(max_exp_num):
    first_round = i==0
    #print("Here it is")
    
    
    tomo, search_param, target_cache_folder, peet_iter, end_signal_c = sta_peet_one(star_file, param_file, tomoName, cpus, first_round)
    #print(tomo, target_cache_folder, search_param, peet_iter, end_signal)
    
    min_count_to_continue = 5

    if end_signal_c <= min_count_to_continue:
        logger.info("no more/too few particles need to be added based on CCC threashold")
        break
    else:
        exp = Expand(tomo=tomo, search_param=search_param, target_cache_folder=target_cache_folder, peet_iter=peet_iter)
        #exp = Expand(tomo, search_param, target_cache_folder="/amber/electron/logicvay2010/003-2019DEC-Archaea/02-M.Hungatei/slayer/relion4/pick/sta/MH_253_cache/round_0", \
        #    peet_iter = 4, threashold_CCC=0.1)
        exp.migrate()
        exp.prepare_exp()
        exp.expand_one()
        if exp.stop_signal:
            logger.info("no more particles need to be added!")
            break
    
    logger.info("Expand for {} at round {}, particle numbers: {}, accepted {}".format(tomo.tomoName, latest_round+i+1, tomo.numberParticles, end_signal_c))

#prepare for the final result
final_result_folder = "{}_final".format(tomo.staPath)
#if os.path.exists(final_result_folder):
#    cmd = "mv {} {}~".format(final_result_folder, final_result_folder)
#    subprocess.run(cmd,shell=True)
#cmd = "mkdir -p {}".format(final_result_folder)
#subprocess.run(cmd,shell=True)
mkfolder(final_result_folder)

cache_folder_path = "{}_cache".format(tomo.staPath)
#latest_round = -1
points = np.array([])
peet_motl_header = "CCC,reserved,reserved,pIndex,wedgeWT,NA,NA,NA,NA,NA,xOffset,yOffset,zOffset,NA,NA,reserved,EulerZ(1),EulerZ(3),EulerX(2),reserved,CREATED WITH PEET Version 1.15.0 10-January-2021\n"
motls = np.array([])
rots = np.array([])
if os.path.exists(cache_folder_path):
    rounds = os.listdir(cache_folder_path)
    for r in rounds:
        exp_path = "{}/{}/exp".format(cache_folder_path, r)
        if os.path.exists(exp_path):
            modfile = "{}/{}.mod".format(exp_path, tomo.tomoName)
            df_mod = imodmodel.read(modfile)
            a = np.vstack((df_mod.x, df_mod.y, df_mod.z))
            if len(points) == 0:
                points = a.transpose()
            else:
                points = np.vstack((points, a.transpose()))

            motlfile_one = open("{}/{}_MOTL.csv".format(exp_path, tomo.tomoName))
            motl_data = np.array(motlfile_one.readlines())
            motlfile_one.close()
            motls = np.hstack((motls, motl_data[1:]))

            rotfile_one = open("{}/{}_RotAxes.csv".format(exp_path, tomo.tomoName))
            rotfile_data = np.array(rotfile_one.readlines())
            rotfile_one.close()
            rots = np.hstack((rots, rotfile_data[:]))


import scipy.cluster.hierarchy as hcluster
#repeat_unit = 12
tomo.readTomo()
search_param = SearchParam(param_file)
#logger.info(search_param.repeating_unit)
#logger.info(tomo.apix)
repeat_unit = round(search_param.repeating_unit/tomo.apix, 1)
#logger.info("repeat_unit: {}".format(repeat_unit))
particle_dup_ratio = 0.8
patch_dis_ratio = 1.5
clusters = hcluster.fclusterdata(points, repeat_unit*particle_dup_ratio, criterion="distance")
points_rmdup = []
motls_rmdup = []
rots_rmdup = []
for i in range(len(set(clusters))):
    #x,y,z = np.mean(points[np.argwhere(clusters == i+1)], axis=0)[0]
    neighbors = np.squeeze(points[np.argwhere(clusters == i+1)], axis=1)
    if len(neighbors) > 1:
        #logger.info(motls[np.argwhere(clusters == i+1)])
        temp_motl = motls[np.argwhere(clusters == i+1)]
        #logger.info(temp_motl_2)
        temp_motl = [motl_line[0].strip().split(',') for motl_line in temp_motl]
        #logger.info(temp_motl)
        temp_motl = np.array([[float(it) for it in item] for item in temp_motl])
        
        #logger.info(temp_motl[:,0])
        #logger.info(temp_motl.max(axis=0)[0])
        #logger.info(np.argwhere(temp_motl[:,0]==temp_motl.max(axis=0)[0]))
        ind = np.argwhere(temp_motl[:,0]==temp_motl.max(axis=0)[0])[0,0]
        #logger.info(ind)
        
        x,y,z = points[np.argwhere(clusters == i+1)[ind][0]]
        #logger.info(points[np.argwhere(clusters == i+1)[ind][0]])
        points_rmdup.append([x,y,z])
        if len(motls_rmdup) == 0:
            motls_rmdup = motls[np.argwhere(clusters == i+1)[ind][0]]
            rots_rmdup = rots[np.argwhere(clusters == i+1)[ind][0]]
        else:
            motls_rmdup = np.hstack((motls_rmdup, motls[np.argwhere(clusters == i+1)[ind][0]]))
            rots_rmdup = np.hstack((rots_rmdup, rots[np.argwhere(clusters == i+1)[ind][0]]))
    else:
        #logger.info(points[np.argwhere(clusters == i+1)])
        x,y,z = points[np.argwhere(clusters == i+1)][0,0]
        points_rmdup.append([x,y,z])
        if len(motls_rmdup) == 0:
            motls_rmdup = motls[np.argwhere(clusters == i+1)[0,0]]
            rots_rmdup = rots[np.argwhere(clusters == i+1)[0,0]]
        else:
            motls_rmdup = np.hstack((motls_rmdup, motls[np.argwhere(clusters == i+1)[0,0]]))
            rots_rmdup = np.hstack((rots_rmdup, rots[np.argwhere(clusters == i+1)[0,0]]))

points_rmdup = np.array(points_rmdup)
clusters_2 = hcluster.fclusterdata(points_rmdup, repeat_unit*patch_dis_ratio, criterion="distance")
points_patch = []
motls_patch = []
rots_patch = []
#min_patch_size = 12
patch_count = 0
for i in range(len(set(clusters_2))):
    neighbors = np.squeeze(points_rmdup[np.argwhere(clusters_2 == i+1)], axis=1)
    if len(neighbors) >= min_patch_size:
        patch_count+=1
        #x,y,z = np.mean(points_rmdup[np.argwhere(clusters_2 == i+1)], axis=0)[0]
        #logger.info(points_rmdup[np.argwhere(clusters_2 == i+1)])
        [points_patch.append([patch_count, p[0][0],p[0][1],p[0][2]]) for p in points_rmdup[np.argwhere(clusters_2 == i+1)]]
        if patch_count==1:
            motls_patch = motls_rmdup[np.argwhere(clusters_2 == i+1)]
            rots_patch = rots_rmdup[np.argwhere(clusters_2 == i+1)]
        else:
            motls_patch = np.vstack((motls_patch, motls_rmdup[np.argwhere(clusters_2 == i+1)]))
            rots_patch = np.vstack((rots_patch, rots_rmdup[np.argwhere(clusters_2 == i+1)]))
            #logger.info(motls_patch.shape)
            #logger.info(rots_patch.shape)
        
clean_pts_file = "{}/{}.pts".format(final_result_folder, tomo.tomoName)
clean_mod_file = "{}/{}.mod".format(final_result_folder, tomo.tomoName)
clean_motlfile = "{}/{}_MOTL.csv".format(final_result_folder,tomo.tomoName)
clean_rotfile = "{}/{}_RotAxes.csv".format(final_result_folder,tomo.tomoName)
with open(clean_pts_file,"w") as clean_pts_file_w:
    with open(clean_motlfile,"w") as fmotl:
        fmotl.write(peet_motl_header)
        with open(clean_rotfile,"w") as frot:
            for i, coord in enumerate(points_patch):
                clean_pts_file_w.write(" ".join([str(int(x)) for x in coord])+"\n")
                
                motl_list = motls_patch[i][0].split(",")
                motl_list[3] = str(i+1)
                motl_line = ",".join(motl_list)

                rot_list = rots_patch[i][0]
                fmotl.write(motl_line)
                frot.write(rot_list)

cmd = "cd {}; point2model {} {} -scat -sphere 5 ".format(final_result_folder, clean_pts_file, clean_mod_file)
subprocess.run(cmd,shell=True, stdout=subprocess.PIPE)

#print(motls)
#print(motls.shape)
#print(rots.shape)
#print(points.shape)
#print(points.shape)
if len(motls) > 0:
    coordfile = "{}/{}_raw.pts".format(final_result_folder,tomo.tomoName)
    modfile = "{}/{}_raw.mod".format(final_result_folder,tomo.tomoName)
    motlfile = "{}/{}_raw_MOTL.csv".format(final_result_folder,tomo.tomoName)
    rotfile = "{}/{}_raw_RotAxes.csv".format(final_result_folder,tomo.tomoName)
    with open(motlfile,"w") as fmotl:
        fmotl.write(peet_motl_header)
    with open(coordfile,"w") as fcoord:
        with open(motlfile,"a") as fmotl:
            with open(rotfile,"w") as frot:
                index = 0
                for i, coord in enumerate(points):
                    index+=1
                    motl_list = motls[i].split(",")
                    motl_list[3] = str(index)
                    motl_line = ",".join(motl_list)

                    rot_list = rots[i]

                    fmotl.write(motl_line)
                    fcoord.write(" ".join([str(int(x)) for x in coord])+"\n")
                    frot.write(rot_list)
    cmd = "cd {}; point2model {} {} -scat -sphere 5 ".format(final_result_folder, coordfile, modfile)
    #cmd = "cd {}; point2model {} {}; rm {}".format(final_result_folder, coordfile, modfile, coordfile)
    subprocess.run(cmd,shell=True, stdout=subprocess.PIPE)

    cmd = "cd {}; ln -s {} ./{}.mrc".format(final_result_folder, tomo.tomogramPickPath, tomo.tomoName)
    subprocess.run(cmd,shell=True, stdout=subprocess.PIPE)
logger.info("Particle numbers {}. After clean {}! with {} patches".format(len(points), len(points_patch), patch_count))
logger.info("The final coords and rotation are saved in the final folder!")
#print("The final coords and rotation are saved in the final folder!")

