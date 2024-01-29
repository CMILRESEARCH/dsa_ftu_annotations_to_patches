# dsa_ftu_annotations_to_patches

Utility script to extract FTU from DSA annotations files and store them as jpg image patches


## Dependencies:

OpenCV

girder_client

tiffslide

## Usage

```console
conda run python main.py --fixedSize True 
	--masked True 
	--svsBase '/blue/...' 
	--fid '659eb008bd96faac30b68fff' 
	--layerName 'non_globally_sclerotic_glomeruli' 
	--outputdir '/blue/...' 
	--username 'username' 
	--password 'password' 
	--apiUrl 'https://athena.rc.ufl.edu/api/v1'
```

## Parameters: 

--fixedSize 	True 	: The software will find the bounding box of maximum size out of all FTU, then extract a patch of fixed sized equal to the size of that bounding box
		False	: Will extract a bounding box with no padding around the FTU
  
--masked	True  	: The saved image will be the patch multiplied by the binary mask
		False	: The saved image will be the patch without multiplying by the binary mask
  
--fid		Folder ID on DSA

--layerName	Annotation layer name on DSA

--outputdir	Directory/Folder to save output, if folder not exists it will be created by the script

--username	Username on DSA Account

--password	Password on DSA Account

--apiUrl	URL to DSA REST API
