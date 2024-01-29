# dsa_ftu_annotations_to_patches

Utility script to extract FTU from DSA annotations files and store them as jpg image patches


## Dependencies:
OpenCV
girder_client
tiffslide

## Usage
conda run python main.py --fixedSize True --masked True --svsBase '</blue/pinaki.sarder/..>' --fid '659eb008bd96faac30b68fff' --layerName 'non_globally_sclerotic_glomeruli' --outputdir '</blue/pinaki.sarder/..>' --username 'username' --password 'password' --apiUrl 'https://athena.rc.ufl.edu/api/v1'
