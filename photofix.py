# encoding: utf-8

import os
import sys

# for file hash calculation
import hashlib

# datetime manipulation
from datetime import datetime

# exif tags
import gi
gi.require_version('GExiv2', '0.10')
from gi.repository import GObject, GExiv2

# for moving files and dirs
import shutil
import errno

# configuration
VALID_IMAGES = set(['.cr2', '.cr3', '.crw', '.dng', '.gpr', '.jpg', '.jpeg', '.png', '.raf', '.tif', '.tiff'])
VALID_VIDEO = set(['.mp4', '.mkv'])

PATH = {
    'image': '/PATH/TO/images',
    'video': '/PATH/TO/video',
    'non-image': '/PATH/TO/non-images',
    'duplicate': '/PATH/TO/duplicates',
    'failed': '/PATH/TO/failed'
}
DUP_COUNTER = 0
TS =  datetime.strftime(datetime.now(), "%Y-%m-%d")
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
    fs_date = datetime.fromtimestamp(os.path.getmtime(filename))
    #print "%s fs_date: %s" % (filename, fs_date.strftime("%s")) # debug
    try:
        exif_date = GExiv2.Metadata(filename).get_date_time()
        #print "%s exif_date: %s" % (filename, exif_date.strftime("%s")) # debug
        # avoid using the epoch if possible
        if (int(fs_date.strftime("%s")) == 0 or fs_date > exif_date):
            return exif_date
        else:
            return fs_date
    except:
        return fs_date


#
# get_file_hash(filename)
# returns the sha256 sum for the file as a string
#
def get_file_hash(filename):
    sha = hashlib.sha256()
    with open(filename, 'rb') as fp:
        buf = fp.read(262144)
        while len(buf) > 0:
            sha.update(buf)
            buf = fp.read(262144)
    return sha.hexdigest()

#
# move_file(filename, destination)
# moves the file and outputs the source and destination for logging
#
def move_file(filename, destination):
    global PATH
    global DUP_COUNTER
    (original_directory, original_filename) = os.path.split(filename)
    (destination_directory, destination_filename) = os.path.split(destination)
    (original_base_filename, original_extension) = os.path.splitext(original_filename)
    destination_hash = destination_filename[16:]

    # if the destination is a directory, rebuild the destination with
    # directory and original filename so it becomes a full path
    if os.path.isdir(destination):
        destination = os.path.join(destination, original_filename)

    # handle destination links
    if os.path.islink(destination):
        print('WARNING: destination', destination, 'is a link, redirecting', filename, 'to failed')
        newdest = os.path.join(PATH['failed'], original_filename)
        return move_file(filename, newdest)

    # handle duplicates
    if os.path.isfile(destination) or destination_hash in EXISTING_FILES:
        print('WARNING:', filename, 'seems like a duplicate, redirecting...')
        DUP_COUNTER += 1
        if (original_filename != destination_filename):
            # if the filenames are different, save the original one for reference
            newdest = os.path.join(PATH['duplicate'], original_base_filename + '_' + str(DUP_COUNTER) + '-' + destination_filename)
        else:
            newdest = os.path.join(PATH['duplicate'], original_base_filename + '_' + str(DUP_COUNTER) + '.' + original_extension)
        return move_file(filename, newdest)

    mkdir_p(destination_directory)
    print('copy to', destination)
    try:
        shutil.copy2(filename, destination)
        if destination_directory.startswith(PATH['image']):
            EXISTING_FILES.add(destination_hash)
    except Exception as e:
        print('WARNING: failed to copy', filename, 'to', destination, '-', e)
        return None
    
    if os.path.isfile(destination):
        try:
            print('removing', filename)
            os.remove(filename)
        except Exception as e:
            print('WARNING: failed to remove', filename, '-', e)

    


#
# explore_path(path)
# recursively iterates on path, moving images around
#
def explore_path(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            fullfn = os.path.join(root, f)

            # skip symlinks and files that have already been moved (eg. xmp files)
            if not os.path.isfile(fullfn): continue

            # save the file name and extension
            # in the base of sidecar files, bn will be the original image
            # /path/to/image.ext.xmp -> /path/to/image.ext + .xmp
            bn, ext = os.path.splitext(fullfn)
            ext = ext.lower()

            # print the file we're working on
            print(fullfn)

            # handle different types of files
            if ext in VALID_IMAGES:
                handle_image(fullfn)
                continue
            elif ext in VALID_VIDEO:
                handle_video(fullfn)
                continue
            elif ext == '.xmp' and os.path.isfile(bn):
                # skip sidecar files with matching images: they will be handled
                # during the original image handling pass
                continue
            else:
                move_file(fullfn, PATH['non-image'])
                continue

        for d in dirs:
            fulldn = os.path.join(root, d)
            # skip symlinks
            if os.path.islink(fulldn): continue
            # recursively calls itself to check the other directories
            explore_path(fulldn)


#
# handle_image(filename)
# renames and moves the single image
#
def handle_image(fullfn):
    # get filename and extension
    dir, fn = os.path.split(fullfn) # dir and filename
    bn, ext = os.path.splitext(fn) # basename and extension
    ext = ext.lower() # lowercase extension

    # recover metadata from the image
    file_date = get_file_datetime(fullfn)
    file_hash = get_file_hash(fullfn)

    # destination is: PATH['image']/TS/YYYYmmdd-HHMMSS_ORIGINAL-FILENAME_HASH.EXTENSION
    destfn = os.path.join(PATH['image'], TS, file_date.strftime("%Y%m%d-%H%M%S") + '--' + bn + '--' + file_hash + ext)

    # move the file
    move_file(fullfn, destfn)

    # if there is an XMP sidecar file, move that as well
    for f in os.listdir(dir):
        f_low = f.lower()
        if f.startswith(fn) and f_low.endswith('.xmp'):
            handle_xmp(os.path.join(dir, f), destfn)


#
# handle_xmp(path_to_xmp_file, path_to_destination_image)
# renames the XMP file and changes the file internal reference name if needed
#
def handle_xmp(path_src_xmp, path_dest_img):
    # get filename and extension
    srcdir, srcxmp = os.path.split(path_src_xmp)   # source dir and filename
    srcimg, ext = os.path.splitext(srcxmp)         # source image and extension
    destdir, destimg = os.path.split(path_dest_img) # destination dir and filename
    path_dest_xmp = path_dest_img + '.xmp'

    # just move the file if the file name is not changing
    if srcimg == destimg:
        move_file(path_src_xmp, path_dest_xmp)
        return True

    # change the filename reference inside the file, if the name changes
    try:
        with open(path_src_xmp, 'r') as file:
            xmp = file.read()

        print('XMP copy to', path_dest_xmp)
        with open(path_dest_xmp, 'w') as file:
            file.write(xmp.replace(srcimg, destimg))

        print('XMP removing', path_src_xmp)
        os.remove(path_src_xmp)

    except Exception as e:
        print('WARNING: failed to handle', path_src_xmp, '-', e)



#
# handle_video(filename)
# recursively iterates on path, moving videos around
#
def handle_video(fullfn):
    # get filename and extension
    fn = os.path.split(fullfn)[1] # filename
    bn, ext = os.path.splitext(fn) # basename and extension
    ext = ext.lower() # lowercase extension

    # recover metadata from the video
    file_date = get_file_datetime(fullfn)

    # destination is: PATH['video']/TS/YYYYmmdd-HHMMSS_HASH.EXTENSION
    destfn = os.path.join(PATH['video'], TS, file_date.strftime("%Y%m%d-%H%M%S") + '_' + bn + ext)
    move_file(fullfn, destfn)



# fai girare sul primo argomento
explore_path(sys.argv[1])
