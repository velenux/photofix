# photofix
Organize your photos by date and metadata.

1. Edit the paths

PATH = {
    'image': '/path/to/image/storage',
    'non-image': '/path/to/non-image/storage',
    'duplicate': '/path/to/duplicates/storage',
    'failed': '/path/to/failed-to-copy/storage'
}

image should point to wherever you want your photos to be stored, the photos
will be renamed in the format PATH['image']/YYYY/mm/YYYYmmdd-HHMMSS_HASH.EXTENSION
where

- YYYY is the year in 4 digits
- mm is the month in 2 digits
- YYYYmmdd-HHMMSS is the full timestamp
- HASH is the sha256 and md5sum hash of the file contents
- EXTENSION is the original extension

2. Run the script

the easiest way is to just run the run.sh script included

./run.sh <directory_to_scan>
