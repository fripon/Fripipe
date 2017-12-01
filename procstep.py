"""Definition of the different process levels of thr FRIPON pipeline.

This file is part of FriPipe
the FRIPON reduction pipeline
18/05/2016
Author : FRIPON, Chiara Marmo, Jeremie Vaubaillon
Copyright : Observatoire de Paris,
            Universite Paris-Sud,
            CNRS,
            FRIPON
"""

import os, math, re, sys, shutil
import glob
import string
import numpy as np
import numpy.ma as ma
from astropy.io.votable import parse
from image import Image
import datetime
from fripipe.path_and_file import scamp_exe,fri_conf_dir,scamp_ASTREFCAT_NAME

prog="(procstep.py) "

"""
Image normalization
"""
def slippymedian(path,nim,mask="",omask="",med=""):
    """Image normalization by applying a slippy median.
    
    Parameters
    ----------
    path : string
        Path where the images are to be found.
    nim : integer
        number of image to take into account.
    mask : string, optional
        input image mask filename, in particular used by SExtractor to extract stars. See also: http://readthedocs.org/projects/sextractor/.
    omask : string, optional
        output mask file name from the slippy median process.
    med : string, optional
        output image median file name
    
    Returns
    -------
    None : 
        All images in path are processed ; output mask are saved,  as well as median images, if option is set.
    """
    prog="(procstep.slippymedian) "
    print prog+'now relocating to ',path
    os.chdir(path)
    listsort = sorted(os.listdir(path))
    cleanlist=[]
    if len(listsort)>1:
        i = 0
        # now cleans the list of file, in case the process has already been launched in the past
        for im in listsort:
            if (os.path.isfile(im) and os.path.islink(im)):
                 cleanlist.append(im)
        listsort=cleanlist
        print prog,'There are : ',len(listsort),' files to consider'
        for im in listsort:
            print prog,'now considering file: ',im
            if (os.path.isfile(im) and os.path.islink(im)):
                imma = Image(im,mask)
                imma.mednorm()
                if i == 0:
                    naxis1 = imma._Image__header['NAXIS1']
                    naxis2 = imma._Image__header['NAXIS2']
                    cube = imma._Image__data
                    medians = imma._Image__median
                else:
                    cube = np.dstack((cube,imma._Image__data))
                    medians = np.vstack((medians,imma._Image__median))
                i = i + 1
        print prog+"Now Computing and subtracting running median."
        i = 0
        for im in listsort:
            if (os.path.isfile(im) and os.path.islink(im)):
                if i < nim/2:
                    jstart = 0
                    jend = nim
                else:
                    jstart = i - math.ceil(nim/2)
                    jend = i + math.ceil(nim/2)
                if jend > len(listsort):
                    jend = len(listsort) - 1
                    jstart = jend - nim - 1
                if jstart < 0:
                    jstart = 0
                jstart = np.int_(jstart)
                jend   = np.int_(jend)
#                print "im=",im," jstart=",jstart," jend=",jend
                m = np.median(cube[:,:,jstart:jend], axis=2)
                imma = Image(im,mask)
                procim = imma
                procim._Image__name = 'p'+im
                procim._Image__data = (cube[:,:,i] - m) * medians[i]
                procim.save()
                if med != "":
                    print prog,'now computing median'
                    medname = med + im
                    medimma = Image(medname,mask)
                    medimma._Image__header = imma._Image__header
                    medimma._Image__data = m
                    medimma.save()
                else:
                    print prog,'median is not computed'
                if omask != "":
                    print prog+'now computing output mask'
                    omname = omask + im
                    omimma = Image(omname,mask)
                    omimma._Image__header = imma._Image__header
                    omimma._Image__data = m
                    omimma.stdcomp()
                    satlev = 3 * omimma._Image__std
                    boolmask = (omimma._Image__data < medians[i]+satlev)
                    omarray = np.ones((omimma._Image__header['NAXIS2'], omimma._Image__header['NAXIS1']))
                    if hasattr(omimma, '_Image__mask'):
                        omarray = omarray * (omimma._Image__mask > 0)
                    omarray = omarray * boolmask
                    omimma._Image__data = omarray
                    omimma.save()
                else:
                    print prog+'output mask is not computed'
                i = i + 1
            else:
                if os.path.isdir(im):
                  continue
                else:
                  print (prog+"Cannot find file: " + im + " in directory " +  os.getcwd())
                  exit()


"""
Image selection on star visibility
"""
def qualitytest(path,mask="",inmask="",confpath="", ahead=""):
    prog="(procstep.qualitytest) "
    print prog+"..."
    print prog,'now moving into directory: ',path
    os.chdir(path)
    qctdir=path+'qcatalogs/'
    pltdir=qctdir+'plots/'
    goodir=qctdir+'good/'
    for dir in [qctdir,pltdir,goodir]:
        if not os.path.isdir(dir):
            print prog,'now making directory: ',dir
            os.mkdir(dir)
    crpix1 = re.compile("CRPIX1")
    crp1array = []
    crpix2 = re.compile("CRPIX2")
    crp2array = []
    for im in glob.glob('p*.fit'):
        if os.path.isfile(im):
            imma = Image(im)
            options = "-CATALOG_NAME "+qctdir + im + ".ldac "
            options = options + "-CATALOG_TYPE FITS_LDAC -DETECT_MINAREA 2 "
            options = options + "-DETECT_THRESH 3 -BACK_SIZE 8 -SATUR_LEVEL 4095 -SATUR_KEY TOTO"
            if inmask != "":
                inmname = inmask + im[1:]
                options = options + " -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE " + inmname
            else:
                if mask!= "":
                    options = options + " -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE " + mask
            imma.sextraction(confpath=confpath,options=options)
            print prog,'now relocating to ',qctdir
            os.chdir(qctdir)
            options = " -CHECKPLOT_TYPE FGROUPS -CHECKPLOT_NAME " + pltdir + "/fg" + im
            options = options + " -ASTREFCAT_NAME " + scamp_ASTREFCAT_NAME # confpath + "/scamp/hip_main_cut3.ldac"
            options = options + " -MOSAIC_TYPE LOOSE -DISTORT_DEGREES 1"
            options = options + " -SOLVE_ASTROM Y -SOLVE_PHOTOM N -XML_NAME " + im + ".xml" 
            options = options + "    "
            imma.scamption(confpath=confpath,ahead=ahead,options=options)
            if os.path.isfile(im + ".xml"):
                votable = parse(im + ".xml")
                table = votable.get_first_table()
                contrast = table.array['XY_Contrast']
                print prog,'image=',im,' contrast=',contrast
                if contrast > 2:
                    # TODO : REMPLACER LES LIGNES SUIVANTES : TESTER L'EXISTENCE DES FICHIERS ET UTILISER LES OUTILS PYTHON : os.symlink
                    ldacfile=im + ".ldac"
                    headfile=im + ".head"
                    flctfile=im + ".fullcat"
                    for f in [ldacfile,headfile,flctfile]:
                        if os.path.isfile(qctdir+f) and not os.path.islink(goodir+f):
                            os.symlink(qctdir+f,goodir+f)
                    #os.system("cd good/ ; ln -s ../" + im + ".ldac .")
                    #os.system("ln -s ../" + im + ".head .")
                    #os.system("ln -s ../" + im + ".fullcat . ; cd ../")
                    with open(im + ".head") as header:
                        for row in header:
                            if crpix1.match(row):
                                value=row.split()
                                crp1array.append(float(value[2]))
                            if crpix2.match(row):
                                value=row.split()
                                crp2array.append(float(value[2]))
            print prog,'now relocating to ../'
            os.chdir("..")
    if len(crp1array) > 0:
        nhead = len(crp1array)
        crpix1med = np.median(crp1array)
        crpix1std = np.std(crp1array)
        crpix2med = np.median(crp2array)
        crpix2std = np.std(crp2array)
        f = open('qcatalogs/good/crpix.dat', 'w')
        head = "#date;crpix1;std1;crpix2;std2;nim\n"
        f.write(head)
        values = os.getcwd() + ";" + str(crpix1med) + ";" + str(crpix1std) \
               + ";" + str(crpix2med) + ";" + str(crpix2std) + ";" + str(nhead)
        f.write(values)
        f.close()

        print "CRPIX1 = " + str(crpix1med) + " STD = " + str(crpix1std)
        print "CRPIX2 = " + str(crpix2med) + " STD = " + str(crpix2std)

"""
Global astrometric solution
"""
def globalastro(path,confpath="", ahead=""):
    prog="(procstep.globalastro) "
    outpath=path+"/scamp/"
    if not os.path.isdir(outpath):
        print prog,'now creating output directory: '+outpath
        os.mkdir(outpath)
    os.chdir(outpath)
    ahead_old=os.path.dirname(ahead)+'/scamp.old'
    scamp_xml=os.path.dirname(ahead)+'/scamp.xml'
    scamp_xml2=os.path.dirname(ahead)+'/scamp2.xml'
    crp1array = []
    crp2array = []
    crp1warray = []
    crp2warray = []
    for dir in glob.glob(path+"??????/processed_*"):
        gooddir = dir + "/qcatalogs/good/"
        if os.path.isdir(gooddir) and (len(os.listdir(gooddir))>1):
            # symlink good catalogs
            listgoodldac=glob.glob(gooddir+'*.ldac')
            print prog,'There are ',len(listgoodldac),'  file in ',gooddir
            for srcf in listgoodldac:
                #print prog,'now trying to symlink ',srcf
                destf=outpath+os.path.basename(srcf)
                # now test if file already exists and is a broken link
                if (os.path.islink(destf) and not os.path.exists(destf)):
                    print prog,'*** Warning: file ',destf,' is a broken link and is now destroyed'
                    os.remove(destf)
                if not os.path.isfile(destf):
                    try:
                        os.symlink(srcf,destf)
                    except:
                        sys.exit(prog+'*** FATAL ERROR: impossible to symlink '+srcf+' into '+outpath+os.path.basename(srcf))
            if os.path.isfile(gooddir + '/crpix.dat'):
                f = open(gooddir + '/crpix.dat', 'r')
                for line in f.readlines():
                    if line[0]!="#":
                        line.rstrip('\n')
                        values = line.split(';')
                        if (float(values[2])>0) and (float(values[4])>0):
                            crp1array.append(float(values[1]))
                            crp1warray.append(1./float(values[2]))
                            crp2array.append(float(values[3]))
                            crp2warray.append(1./float(values[4]))
                f.close()
        else:
            continue 
    if np.any(crp1warray) and np.any(crp2warray):
        crpix1avg = np.average(crp1array,weights=crp1warray)
        crpix2avg = np.average(crp2array,weights=crp2warray)
    else:
        crpix1avg = 960
        crpix2avg = 640
    # copy scamp ahead file
    crpix1 = re.compile("CRPIX1")
    crpix2 = re.compile("CRPIX2")

    if ahead!= "":
        ahead_old=os.path.dirname(ahead)+'/scamp.old'
        os.system("cp "+ahead+" "+ahead_old)
        #try:
        #    shutil.copy(ahead,ahead_old) 
        #except:
        #    sys.exit(prog+'*** FATAL ERROR: impossible to copy file '+ahead+' into '+ahead_old)
        # now gets the crpix values and update the scamp.ahead file
        fin = open('scamp.old', 'r')
        fout = open('scamp.ahead','w')
        for line in fin.readlines():
            if (not crpix1.match(line) and not crpix2.match(line)):
                fout.write(line)
            elif (crpix1.match(line)):
                fout.write("CRPIX1  = " + str(crpix1avg) + "\n")
            elif (crpix2.match(line)):
                fout.write("CRPIX2  = " + str(crpix2avg) + "\n") 
        fin.close()
        fout.close()

    os.system("mkdir -p plots")
    confarg = "-c " +  fri_conf_dir + "scamp/scamp.conf"
    astrefcat = " -ASTREFCAT_NAME " + scamp_ASTREFCAT_NAME 
    nbad = 1
    while nbad:
        try:
            os.system(scamp_exe + " *.ldac " + confarg + astrefcat)
            if os.path.isfile(scamp_xml):
                votable = parse(scamp_xml)
                table = votable.get_first_table()
                contrast = (table.array['XY_Contrast']).data
                catname = (table.array['Catalog_Name']).data
                nbad = 0
                for i in range(len(contrast)):
                    if contrast[i] < 2:
                        os.system("rm " + catname[i])
                        nbad +=1
                a = zip(contrast,catname)
                a.sort()
                filename, file_extension = os.path.splitext(a[-1][1])
                if os.path.isfile(filename + ".head"):
                    cd = re.compile("CD")
                    crpix = re.compile("CRPIX")
                    os.system("mv "+ahead+ " "+ahead_old) 
                    fgood = open(filename + ".head",'r')
                    fout = open('scamp.ahead','w')
                    fout.write("EQUINOX = 2000.0\n")
                    fout.write("CTYPE1  = 'RA---ARC'\n")
                    fout.write("CTYPE2  = 'DEC--ARC'\n")
                    for line in fgood.readlines():
                        if (cd.match(line)):
                            fout.write(line)
                        if (crpix.match(line)):
                            fout.write(line)
                    fout.write("END")
                    fout.close()
                    fgood.close()

                nbad2 = 1
                while nbad2:
                    try:
                        os.system(scamp_exe + " *.ldac -XML_NAME " + scamp_xml2 + " " + confarg + astrefcat)        
                        if os.path.isfile(scamp_xml2):
                            votable = parse(scamp_xml2)
                            table = votable.get_first_table()
                            contrast = (table.array['XY_Contrast']).data
                            catname = (table.array['Catalog_Name']).data
                            nbad2 = 0
                            for i in range(len(contrast)):
                                if contrast[i] < 2:
                                    os.system("rm " + catname[i])
                                    nbad2 +=1
                    except:
                        print ("I can't run SCAMP!")
                        break

        except:
            print ("I can't run SCAMP!")
            break

    # Running SCAMP for diagnosis
    print ("Running SCAMP for diagnosis")
    for hd in glob.glob('p*.head'):
        ahd = string.replace(hd, ".head", ".ahead")
        os.system("ln -s " + hd + " " + ahd)
    try:
        options = " -FULLOUTCAT_TYPE ASCII_HEAD -FULLOUTCAT_NAME " + (datetime.date.today()).strftime('%Y%m%d') + ".fullcat"
        options = options + " -SOLVE_ASTROM N -SOLVE_PHOTOM N -CHECKPLOT_DEV NULL"
        os.system(scamp_exe + " *.ldac -XML_NAME diagnosis.xml " + confarg + astrefcat + options)
    except:
        print ("I can't run SCAMP!")
    # TODO : UTILISER LES OUTILS PYTHON : os.remove
    os.system("rm p*.ahead")
