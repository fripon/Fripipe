"""Fills the FRIPON database image table with the images in a given directory.


This file is part of FriPipe, the FRIPON reduction pipeline
18/05/2016

Author : FRIPON team

Copyright : Observatoire de Paris, Universite Paris-Sud, CNRS, FRIPON

Free licence

"""

import psycopg2
import socket
import os
import astropy
from astropy.io import fits
from fripipe.private.passwords import Database as db

def fill(inpath):
    """Fills the FRIPON database image table with the images in a given directory.
    
    Parameters
    ----------
    inpath : string
        Directory where images are located.
    
    Returns
    -------
    None :
        The names of the image file in the inpath directory are added to the image table of the FRIPON database.
    
    """
    prog="(fillimagetable.fill) "
    print (prog+"Inserting images in fripon database.")
    
    # Connect to fripon database
    conn = psycopg2.connect(host=db.host, dbname=db.dbname, user=db.user, password=db.password)

    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Select last id value inserted
    cur.execute("SELECT max(idimage) from images;")
    res = cur.fetchone()
    nextid = res[0]

    if nextid == 0:
        nextid = 1;
    else:
        nextid = nextid + 1;

    os.chdir(inpath)
    server = socket.getfqdn()
    listim = os.listdir(inpath)
    i = 0
    n = 0
    nerr = 0
    nwarn = 0
    for im in listim:
        if os.path.isfile(im):

            # Verifying that image is not already inserted
            cur.execute("""SELECT COUNT(*) FROM images WHERE "image_name"=%s;""", (im,))
            res = cur.fetchone()
            if (res[0] != 0):
                print prog,"WARNING: image ", im, " already inserted"
                nwarn = nwarn + 1
                continue

            # Testing file format
            try:
                hdulist = fits.open(im)
                dateobs = hdulist[0].header['DATE-OBS']
                station = hdulist[0].header['TELESCOP']
                naxis = hdulist[0].header['NAXIS']
                hdulist.close()

                # Extracting the format id
                if naxis == 2:
                    cur.execute("""SELECT idimformats FROM imformats WHERE "format"='FITS2D'""")
                if naxis == 3:
                    cur.execute("""SELECT idimformats FROM imformats WHERE "format"='FITS3D'""")
                idfmt = cur.fetchone();
            except IOError:
                print prog+"I/O ERROR: ", im, " is not a FITS file!"
                nerr = nerr + 1
                continue

            # Extracting the station id
            cur.execute("""SELECT idstations FROM stations WHERE "locstations"=%s""", (station,))
            idstation = cur.fetchone();

            # Pass data to fill a query placeholders and let Psycopg perform
            # the correct converURANOSCOPE_sion (no more SQL injections!)
            cur.execute("""INSERT INTO images ("idimage", "image_name", "image_path",
                "image_server", "image_dateobs", "stations_idstations", "imformats_idimformats",
                "events_idevents") VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""", (nextid, im, inpath, server, dateobs, idstation, idfmt,'0'))
            nextid = nextid + 1
            n = n + 1

    cur.execute("""select setval('if_idimage_seq', %s);""", (nextid,))
    # Make the changes to the database persistent
    conn.commit()

    # Close communication with the database
    cur.close()
    conn.close()

    print prog,"Inserted images : ", n
    print prog,"Warning in insertion : ", nwarn
    print prog,"Error in insertion : ", nerr


def update(inpath):
    """Updates the FRIPON database image table with the images in a given directory.
    
    Parameters
    ----------
    inpath : string
        Directory where images are located.
    
    Returns
    -------
    None :
        The names of the image file in the inpath directory are updated to the image table of the FRIPON database.
    
    """
    prog="(fillimagetable.update) "
    print ("Updating images in fripon database.")
    
    # Connect to fripon database
    conn = psycopg2.connect(host=db.host, dbname=db.dbname, user=db.user, password=db.password)
    
    # Open a cursor to perform database operations
    cur = conn.cursor()
    
    os.chdir(inpath)
    server = socket.getfqdn()
    listim = os.listdir(inpath)
    i = 0
    n = 0
    nerr = 0
    nwarn = 0
    for im in listim:
        if os.path.isfile(im):
            continue
    
    # Make the changes to the database persistent
    conn.commit()
    
    # Close communication with the database
    cur.close()
    conn.close()
    
    print prog,"Updated images : ", n
    print prog,"Warning in update : ", nwarn
    print prog,"Error in update : ", nerr

