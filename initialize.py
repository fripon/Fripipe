"""
15/03/2016
Author : FRIPON project
Copyright : Observatoire de Paris, FRIPON
Free license

Purpose: 
 -Initializes fundamental data for the FRIPON pipeline
 -load spice kernels

"""
import os, sys
import numpy as np
import astropy.units as u
import spiceypy as sp
import numpy as np


class path_and_file (object):
    # performs check of existence of directories and files
    check = 1
    # control =1 for debug purpose
    fri_debug = 0
    
    # FRIPON  data directory
    # data directory
    data_dir = '/data/'
    # svn path
    svn_path = data_dir+'friponsvn/'
    # stations directory
    fri_station_dir = data_dir+'stations/'
    # station metadata directory
    fri_meta_dir = data_dir + 'metadata/'
    # processed calibration images directory
    fri_proc_dir = data_dir + 'processed/stations/'
    # detections director
    fri_detect_dir = data_dir+'detections/'
    # multiple detections directory
    fri_data_dir = fri_detect_dir+'multiple/'
    
    # OTHER METEOR MEASUREMENTS-FORMAT directory
    # MetRec data dir. (S. Molau, IMO)
    MetRec_dir = fri_detect_dir+'/MetRec/'
    # UFOAnalyzer data dir. (SonotaCo, NMS)
    UFO_dir = fri_detect_dir+'/UFOAnalyzer/'
    # UWO data dir. (R. Weryk, D. Vida, UWO)
    UWO_dir = fri_detect_dir+'/UWO/'
    # CAMS data dir. (P. Gural, P. Jenniskens)
    CAMS_dir = fri_detect_dir+'/CAMS/'
    
    # fripipe directory
    fri_pipeline_path = svn_path+'/fripipe/'
    # fripipe data directory
    fri_pipeline_data_path = svn_path+'/fripipe_data/'
    # fripipe configuration directory
    fri_conf_dir = fri_pipeline_path+'conf/'
    # fripipe AFM configuration directory
    fri_conf_afm_dir = fri_conf_dir+'AFM/'
    # fripipe scripts directory
    fripipe_script_path = svn_path+'scripts/'
    # fripipe shell script directory
    fripipe_shell_path = fripipe_script_path+'shell/'
    # fripipe topographic data directory
    topo_data_path = fri_pipeline_data_path+'Topography/'
    # fripipe French IGN topographic data directory
    topo_IGN_data_path = topo_data_path+'IGN/MNT/'
    # fripipe All weather data directory
    weather_data_path = fri_pipeline_data_path+'Weather/'
    # MeteoFrance weather directory
    MeteoFrance_path = weather_data_path+'MeteoFrance/'
    # MeteoFrance weather data directory
    MeteoFrance_data_path = MeteoFrance_path+'Data/'
    # University of Wyoming weather data directory
    UWyoming_path = weather_data_path+'/UWyoming/'
    # University of Wyoming weather data directory
    UWyoming_data_path = UWyoming_path+'Data/'
    # University of Wyoming weather data directory
    UWyoming_station_file = UWyoming_path+'snstns.tbl'
    # SPICE librairy executable directory:
    # useful to generate frame kernels of the stations
    # and instrument kernels of the cameras
    spice_exe_path = fri_pipeline_path+'spicexe/'
    
    # SExtractor program
    sex_exe = '/usr/bin/sextractor '
    # SCAMP program
    scamp_exe = '/usr/local/bin/scamp '
    # SCAMP star catalog
    scamp_ASTREFCAT_NAME = fri_conf_dir + 'scamp/hip_main_cut3.ldac '
    
    # private directory
    private_dir = ''.join([fri_pipeline_path,'/private/'])
    
    # work paths
    # work data directory
    work_data_dir = data_dir
    # pipeline Fakeor directory
    fripipe_fakeor_path = fri_pipeline_path+'fakeor/'
    # data detection directory
    work_detc_dir = work_data_dir+'detections/'
    # data multiple detection data directory
    work_mult_dir = work_detc_dir+'multiple/'
    # data Fakeor directory
    work_fake_dir = work_data_dir+'Fakeor/'
    # data meteor entry simulation directory
    work_simu_dir = work_fake_dir+'AFM_simul/'
    # pipeline F90 directory
    fripipe_f90_path = fripipe_fakeor_path+'F90/'
    # pipeline radiant F90 program
    work_radiant_exe = fripipe_f90_path+'radiant'
    # pipeline fakeor simulation program directory
    work_afm_dir = fripipe_fakeor_path+'AFM/'
    # fakeor simulation program executable file
    work_afm_exe = work_afm_dir+'exe/AFM.x'
    # fakeor data directory
    data_fakeor_dir = 'Fakeor/'
    # fakeor default simulation configuration file
    work_simu_cnf = fri_conf_afm_dir+'4FRIPON.cnf'
    
    # SPICE
    # path to SPICE kernels
    kernel_path = fri_pipeline_path+'/conf/kernels/'
    # spice meta-kernel to load
    spicekernel = kernel_path+'standard.ker'
    # loads spice meta-kernel
    sp.furnsh(spicekernel)
    # Note: the FRIPON metakernel is loaded in the private section of the code
    
    # FRIPON camera data features
    # dimension of detector in pixels
    fri_detector_dim =[1000,1000]*u.pix
    # number of frame per second
    fri_fps = 30.0 / u.s
    # mean astrometry precision reached by the measurement CHANGE THIS!!!
    fri_astro_acc_pix = 0.1*u.pix
    # mean astrometry precision reached by the measurement CHANGE THIS!!!
    fri_astro_acc_deg =0.1*u.deg
    # Limiting Magnitude CHANGE THIS!!!
    fri_LimMag =0.0*u.mag
    
    # Fakeor noise law
    # fakeor systematic noise law. choice is: 'sin'
    fkr_noise_law ="sin"
    # fakeor systematic noise value
    fkr_noise_acc =1.0/60.0*u.deg
    
    
    # tests of existence of the paths and files
    if check:
        must_dirs = [data_dir,svn_path,fri_station_dir,fri_detect_dir,fri_data_dir,
                 fri_conf_dir,spice_exe_path,fri_pipeline_path,fri_pipeline_data_path,
                 work_data_dir,fri_pipeline_path,work_detc_dir,work_mult_dir]
        opt_dirs  = [
                 topo_data_path,weather_data_path,fripipe_script_path,
                 fripipe_shell_path,fri_conf_afm_dir,
                 fripipe_fakeor_path,work_fake_dir,
                 work_simu_dir,fripipe_f90_path,work_afm_dir,
                 MeteoFrance_data_path,UWyoming_data_path,
                 MetRec_dir,UFO_dir,UWO_dir,CAMS_dir]
        must_file = [spicekernel]
        opt_file  = [work_afm_exe,work_radiant_exe,work_simu_cnf,
                 UWyoming_station_file]
    
        for path in must_dirs:
            if not os.path.isdir(path):
                sys.exit(prog+'*** FATAL ERROR: directory '+path+
                        ' does not exist')
        for fil in must_file:
            if not os.path.isfile(fil):
                sys.exit(prog+'*** FATAL ERROR: file '+fil+
                        ' does not exist')
        for path in opt_dirs:
            if not os.path.isdir(path):
                print prog+'*** WARNING: directory '+path+' does not exist'
        for fil in opt_file:
            if not os.path.isfile(fil):
                print prog+'*** WARNING: file '+fil+' does not exist'



# set some useful variables
class constants (object):
    # acceleration of gravity at the equator
    g_equ = 9.780 * u.m / u.s/u.s
    # acceleration of gravity at the pole
    g_pol = 9.8321849378*u.m/u.s/u.s
    # acceleration of gravity at 45deg lat
    g_45 = 9.8306 *u.m/u.s/u.s
    # acceleration of gravity [m/s/s]
    g = 9.81 *u.m/u.s/u.s
    # (mean) Earth angular velocity [rad/s]
    w_pla = (2*np.pi)/86164.0 *u.rad/u.s
    # Earth equatorial radius [m], from SPICE
    R_pla = sp.bodvrd( "EARTH", "RADII", 3)[1][0]*u.km
    # shape of the Earth ellipsoid [m,m,m], from SPICE
    abc_pla = sp.bodvrd("EARTH","RADII",3)[1]*u.km
    # flatness coefficient (frmm SPICE)
    f_pla = (abc_pla[1]-abc_pla[2])/abc_pla[1]
    # default meteoroid volumic mass [kg/m^3]
    rhometeor = 3000.0 * u.kg/(u.m*u.m*u.m)
    # altitude below which the Dark Flight is computed
    max_alt_DF = 40*u.km
    # Dark Flight: integration step in altitude [m]
    dh = -100.0 *u.m
    # altitude below which the height above ground is computed (DrkFlgt)
    gnd_alt_thld = 5000.0*u.m
    # default number of clones for the dark flight computation
    nclone	= 10
