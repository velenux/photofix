# photofix

Organize your photos by date and metadata.

## Install

On the latest Mint, I had to install:

```
aptitude install python-pyexiv2 exiv2 libgexiv2-2 libgexiv2-dev
```

## Edit the paths

```
PATH = {
    'image': 'storage/images',
    'video': 'storage/video'
    'non-image': 'storage/non-images',
    'duplicate': 'storage/duplicates',
    'failed': 'storage/failed'
}
```

`image` should point to wherever you want your photos to be stored, the photos
will be renamed in the format `PATH['image']/YYYY/mm/YYYYmmdd-HHMMSS_HASH.EXTENSION`
where

- `YYYY` is the year in 4 digits
- `mm` is the month in 2 digits
- `YYYYmmdd-HHMMSS` is the full timestamp
- `HASH` is the sha256 and md5sum hash of the file contents
- `EXTENSION` is the original extension

`non-image` should point to wherever you want your non-image files to be stored

`duplicate` should point to wherever you want duplicate files to be stored:
duplicates are **not** automatically deleted and their names will be changed
to make sure you don't have clashes

`failed` should point to wherever you want to store files that the script
could not move for whatever reason


## Run the script

the easiest way is to just run the run.sh script included

```
./run.sh <directory_to_scan>
```
