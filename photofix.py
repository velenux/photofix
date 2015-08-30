# encoding: utf-8

import os
import sys

# for file hash calculation
import hashlib

# datetime manipulation
from datetime import datetime

# exif tags
from gi.repository import GExiv2

# for moving files and dirs
import shutil

# configuration
VALID_IMAGES = set(['.cr2', '.png', '.jpg', '.jpeg', '.tif', '.tiff'])
PATH = {
    'image': '/path/to/image/storage',
    'non-image': '/path/to/non-image/storage',
    'duplicate': '/path/to/duplicates/storage',
    'failed': '/path/to/failed-to-copy/storage'
}
DUP_COUNTER = 0
EXISTING_FILES = set([])


#
# useful function from
# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
#
def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc: # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else: raise

#
# get_file_datetime(filename)
# retrieves the EXIF date, falls back to filesystem date
#
def get_file_datetime(filename):
    fs_date   = datetime.fromtimestamp(os.path.getmtime(filename))
    try:
        exif_date = GExiv2.Metadata(filename).get_date_time()
        if (fs_date > exif_date):
            return exif_date
        else:
            return fs_date
    except:
        return fs_date


#
# get_file_hash(filename)
# returns a string made by the sha256 and md5 sum hexdigests of the file contents
#
def get_file_hash(filename):
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    with open(filename, 'rb') as fp:
        buf = fp.read(262144)
        while len(buf) > 0:
            sha.update(buf)
            md5.update(buf)
            buf = fp.read(262144)
    return "%s-%s" % (sha.hexdigest(), md5.hexdigest())

#
# move_file(filename, destination)
# moves the file and outputs the source and destination for logging
#
def move_file(filename, destination):
    (original_directory, original_filename) = os.path.split(filename)
    (destination_directory, destination_filename) = os.path.split(destination)
    (original_base_filename, original_extension) = os.path.splitext(filename)

    # if the destination is a directory, rebuild the destination with
    # directory and original filename so it becomes a full path
    if os.path.isdir(destination):
        destination = os.path.join(destination, original_filename)

    # debug
    print "Preparing to move %s to %s ..." % (filename, destination)

    # handle destination links
    if os.path.islink(destination):
        print "WARNING: destination %s is a link, redirecting %s to failed" % (destination, filename)
        newdest = os.path.join(PATH['failed'], original_filename)
        return move_file(filename, newdest)

    # handle duplicates
    if os.path.isfile(destination) or destination_filename in EXISTING_FILES:
        print "WARNING: %s seems like a duplicate, redirecting..." % (destination, filename)
        if (original_filename != destination_filename):
            newdest = os.path.join(PATH['duplicate'], "%s_%s-%s" % (original_base_filename, DUP_COUNTER, destination_filename))
        else:
            newdest = os.path.join(PATH['duplicate'], "%s_%s.%s" % (original_base_filename, DUP_COUNTER, original_extension))
        return move_file(filename, newdest)

    # mkdir_p(destination_directory)
    print "%s -> %s" % (filename, destination)
    #try:
    #   shutil.move(filename, destination)
    #   if destination_directory.startswith(PATH['image']):
    #       EXISTING_FILES.add(destination_filename)
    #except:
    #   print "WARNING: failed to copy %s to %s, redirecting to failed..." % (filename, destination)
    #

#
# find_images(path)
# recursively iterates on path, moving images around
#
def find_images(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            fullfn = os.path.join(root, f)

            # skip symlinks
            if os.path.islink(fullfn): continue

            # save the file extension
            ext = os.path.splitext(fullfn)[1].lower()

            # move non-image files to another place and continue to the next file
            if not ext in VALID_IMAGES:
                move_file(fullfn, PATH['non-image'])
                continue

            # recover metadata from the image
            file_date = get_file_datetime(fullfn)
            file_hash = get_file_hash(fullfn)

            # destination is: PATH['image']/YYYY/MM/HASH.EXTENSION
            destfn = os.path.join(PATH['image'], file_date.strftime("%Y"), file_date.strftime("%m"), file_hash + ext)
            move_file(fullfn, destfn)

        for d in dirs:
            fulldn = os.path.join(root, d)
            # skip symlinks
            if os.path.islink(fulldn): continue
            #
            find_images(fulldn)

# fai girare sul primo argomento
find_images(sys.argv[1])
