import cv2

import girder_client
import shapely
import tiffslide as openslide
import numpy as np
import os
import logging

import numpy as np

import argparse

class DSA:
    def __init__(self, config) -> None:
        self.config = config
        apiUrl = config['apiUrl']
        username = config['username']
        password = config['password']
        self.gc = girder_client.GirderClient(apiUrl=apiUrl)
        self.gc.authenticate(username, password)

class DSAFolder(DSA):
    def __init__(self, config) -> None:
        super().__init__(config)
        folderid = config['fid']
        self.items = self.getItemsInDsaFolder(folderid)

    def getItemsInDsaFolder(self, dsaFolder):
        method = "GET"
        path = f"/item"
        r = self.gc.sendRestRequest(method, path, {'folderId': dsaFolder, 'limit': 1000})
        items = [(f['_id'], f['name']) for f in r if f['name'].endswith('.svs')]
        return items

class DSAItem(DSA):
    def __init__(self, config, fid, svsname) -> None:
        super().__init__(config)
        self.layerName = config['layerName']
        self.fid = fid
        self.svsname = svsname
        self.name = svsname.replace('.svs', '')
        self.svsBase = config['svsBase']
        self.annotations = self.convertAnnotations(self.getAnnotationByLayerName(self.fid, self.layerName))
        self.s = openslide.open_slide(f"{self.svsBase}/{self.svsname}")

    def getAnnotationByLayerName(self, id, name):

        method = "GET"
        path = f"/annotation"
        r = self.gc.sendRestRequest(method, path, {'itemId': id, 'limit': 1000})

        for anno in r:
            if anno['annotation']['name'] ==  name or anno['annotation']['name'] ==  f" {name}"or anno['annotation']['name'] ==  f"  {name}" :
                annoId = anno['_id']

        method = "GET"
        path = f"annotation/{annoId}"
        annotations = self.gc.sendRestRequest(method, path, {'id': annoId, 'limit': 10000000})
        return annotations

    def convertAnnotations(self, anno):
        annos = anno['annotation']['elements']
        annos_2 = []
        for a in annos:
            try:
                annos_2.append([(k[0], k[1]) for k in a['points']])
            except:
                pass
        annos_ = []
        for k in annos_2:
            if len(k)>4:
                annos_.append(shapely.Polygon(k))
        return annos_
    
    def extract(self):
        outputdir = self.config['outputdir']

        if not os.path.exists(outputdir):
            os.mkdir(outputdir)
        
        for i in range(len(self.annotations)):
            try:
                patch, mask = self.getPatchMask(i)
                if self.config['masked']:
                    out = np.array(patch*(mask/255), dtype='uint8')
                else:
                    out = np.copy(patch)
                cv2.imwrite(f'{outputdir}/{self.name}_{i}_{self.x}_{self.y}.jpg', out)
            except:
                pass

    def extractFixed(self, w, h):
        outputdir = self.config['outputdir']

        if not os.path.exists(outputdir):
            os.mkdir(outputdir)
        
        for i in range(len(self.annotations)):
            try:
                patch, mask = self.getPatchMaskFixed(i, w, h)
                if self.config['masked']:
                    out = np.array(patch*(mask/255), dtype='uint8')
                else:
                    out = np.copy(patch)
                cv2.imwrite(f'{outputdir}/{self.name}_{i}_{self.x}_{self.y}.jpg', out)
            except:
                pass

    def getMaxBB(self):
        
        w_max = 0
        h_max = 0
        for i in range(len(self.annotations)):
            try:
                w, h = self.getWH(i)
                w_max = max(w, w_max)
                h_max = max(h, h_max)
            except:
                pass
        return w_max, h_max

    def getWH(self, tid):
        polygon1 = self.annotations[tid]
        bb = polygon1.bounds
        w = int(bb[2]-bb[0])
        h = int(bb[3]-bb[1])
        
        return w, h

    def getPatchMask(self, tid):
        polygon1 = self.annotations[tid]
        x,y = polygon1.exterior.xy
        bb = polygon1.bounds

        size_1 = [int(bb[3]-bb[1]), int(bb[2]-bb[0])]

        mask = np.zeros(size_1)

        points = [[int(x-bb[0]), int(y-bb[1])] for x, y in zip(*polygon1.boundary.coords.xy)]

        mask = cv2.fillPoly(mask, np.array([points]).astype(np.int32), color=255)

        size_2 = [int(bb[2]-bb[0]), int(bb[3]-bb[1])]
        location = (int(bb[0]), int(bb[1]))

        self.x = int(bb[0])
        self.y = int(bb[1])

        level = 0

        patch = np.array(self.s.read_region(location, level, size_2))[:,:,:3]
        mask = cv2.cvtColor(np.array(mask, dtype='uint8'), cv2.COLOR_GRAY2RGB)
        
        return patch, mask
    
    def getPatchMaskFixed(self, tid, w, h):
        polygon1 = self.annotations[tid]
        x,y = polygon1.exterior.xy
        bb = polygon1.bounds

        size_2 = [int(bb[2]-bb[0]), int(bb[3]-bb[1])]

        wd = max((w - int(bb[2]-bb[0]))//2, 0)
        hd = max((h - int(bb[3]-bb[1]))//2, 0)

        size_2 = [int(bb[2]-bb[0])+2*wd, int(bb[3]-bb[1])+2*hd]

        location = (int(bb[0])-wd, int(bb[1])-hd)

        self.x = int(bb[0])-wd
        self.y = int(bb[1])-hd

        level = 0

        patch = np.array(self.s.read_region(location, level, size_2))[:,:,:3]

        size_1 = [int(bb[3]-bb[1])+2*hd, int(bb[2]-bb[0])+2*wd]

        mask = np.zeros(size_1)

        points = [[int(x-bb[0]+wd), int(y-bb[1]+hd)] for x, y in zip(*polygon1.boundary.coords.xy)]

        mask = cv2.fillPoly(mask, np.array([points]).astype(np.int32), color=255)

        mask = cv2.cvtColor(np.array(mask, dtype='uint8'), cv2.COLOR_GRAY2RGB)
        
        return patch, mask

# Pipeline
def pipeline(config):

    dsaFolder = DSAFolder(config)
    items = dsaFolder.items

    w_max = 0
    h_max = 0
    for i in range(len(items)):
        try:
            logging.warning(f'Processing slide # {i}!')

            fid, svsname = items[i]
            item = DSAItem(config, fid, svsname)

            if config['fixedSize']:
                w, h =  item.getMaxBB()
                w_max = max(w, w_max)
                h_max = max(h, h_max)
        except:
            logging.warning('Skip Accessing Loop 1 : {i}')

    for i in range(3):
        try:
            fid, svsname = items[i]
            item = DSAItem(config, fid, svsname)

            item.extractFixed(w_max, h_max)
        except:
            logging.warning('Skip Accessing Loop 2 : {i}')

parser = argparse.ArgumentParser(
                    prog='DSA FTU Annotations to Patches',
                    description='Extract DSA FTU Annotations to Patches',
                    epilog='Text at the bottom of help')

parser.add_argument('--svsBase', help='/blue/pinaki.sarder/...')     
parser.add_argument('--fid', help='659eb008bd96faac30b68fff')     
parser.add_argument('--layerName', help='non_globally_sclerotic_glomeruli')     
parser.add_argument('--outputdir', help='/orange/pinaki.sarder/ahmed.naglah/...')     
parser.add_argument('--username', help='username')     
parser.add_argument('--password', help='password')     
parser.add_argument('--apiUrl', help='https://athena.rc.ufl.edu/api/v1')     
parser.add_argument('--masked', help='Apply ftu mask on patch')     
parser.add_argument('--fixedSize', help='Extract fixed sized with max w and h')     

args = parser.parse_args()

config = {
    'svsBase' : args.svsBase,
    'fid' : args.fid,
    'layerName': args.layerName,
    'outputdir': args.outputdir,
    'username': args.username,
    'password': args.password,
    'apiUrl': args.apiUrl,
    'masked': args.masked,
    'fixedSize': args.fixedSize,
}

logging.warning('Starting pipeline!')

pipeline(config)

if __name__=='__main__':

    config = {
        'svsBase' : "/blue/pinaki.sarder/...",
        'fid' : "659eb008bd96faac30b68fff",
        'layerName': 'non_globally_sclerotic_glomeruli',
        'outputdir': '/orange/pinaki.sarder/ahmed.naglah/...',
        'username': 'username',
        'password': 'password',
        'apiUrl': 'https://athena.rc.ufl.edu/api/v1',
        'masked': True,
        'fixedSize': True,
    }

    pipeline(config)
