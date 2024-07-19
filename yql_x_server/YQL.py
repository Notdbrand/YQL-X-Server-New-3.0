import json
import mmap
import os
import re
import threading
from pathlib import Path
from yql_x_server.args import args

class YQL:
    def __init__(self):
        # Load json into memory
        self.json_disk_file = open(Path(args.geo_database_path), "r")
        if os.name == 'nt':
            self.json_mem_file = mmap.mmap(self.json_disk_file.fileno(), 0, access=mmap.ACCESS_READ)
        else:
            self.json_mem_file = mmap.mmap(self.json_disk_file.fileno(), 0, prot=mmap.PROT_READ)
        self.json_disk_file.close()
        self.json_file = json.load(self.json_mem_file)
        self.generatedFileLock = threading.Lock()

    def getWoeidsInQuery(self, q, formatted=False):
        if formatted:
            return [q] if not isinstance(q, list) else q
        woeids = []
        for woeid in re.findall(r'\b\d+\b', q):
            if not woeid in woeids:
                woeids.append(woeid)
        return woeids
    
    def getWoeidFromName(self, name):
        if not name:
            print("Name is empty")
            return "000000"
        print("Getting woeid from name, " + name)
        try:
            result = self.getSimilarName(name)[0]['woeid']
            print("Woeid from name is " + result)
            return result
        except:
            # Generate woeid from name, store the characters in unicode int format for decoding later
            print("Generating woeid from name, " + name)
            with self.generatedFileLock:
                generatedFile = open("generatedWoeids.json", "r+")
                generatedWoeids = json.load(generatedFile)
                woeid = ""
                woeidArray = []
                for letter in name:
                    unicode = str(ord(letter))
                    woeid += unicode
                    woeidArray.append(unicode)
                if not any(woeid in v for v in generatedWoeids):
                    print("Adding woeid to generatedWoeids.json")
                    generatedWoeids.update({woeid: woeidArray})
                    generatedFile.seek(0)
                    generatedFile.write(json.dumps(generatedWoeids))
                    generatedFile.truncate()
                else:
                    print("Woeid already in generatedWoeids.json")
                generatedFile.close()
                return woeid

    def getNamesForWoeidsInQ(self, q, formatted=False, nameInQuery=False):
        names = []
        if not nameInQuery:
            woeids = self.getWoeidsInQuery(q, formatted)
        else:
            return [q[q.find("query='")+7:q.find(", ")]]
        try:
            for woeid in woeids:
                names.append(self.json_file["woeid"][woeid])
        except Exception as e:
            generatedFile = open(Path(args.generated_woeids_path), "r")
            generatedWoeids = json.load(generatedFile)
            if not generatedWoeids:
                return []
            for woeid in woeids:
                name = ""
                for unicodeChar in generatedWoeids[woeid]:
                    name += chr(int(unicodeChar))
                names.append(name)
        return names
       
    def getSimilarName(self, q):
        resultsList = []
        for i in self.json_file["small"].items():
            if q.lower() in i[0].lower():
                resultsList.append({
                    "name": i[0],
                    "iso": self.json_file["small"][i[0]][1],
                    "woeid": self.json_file["small"][i[0]][0],
                    "type": "small"
                })
        for i in self.json_file["city"].items():
            if q.lower() in i[0].lower() and not i[0] in resultsList:
                resultsList.append({
                    "name": i[0],
                    "iso": self.json_file["city"][i[0]][1],
                    "woeid": self.json_file["city"][i[0]][0],
                    "type": "city"
                })
        for i in self.json_file["state"].items():
            if q.lower() in i[0].lower() and not i[0] in resultsList:
                resultsList.append({
                    "name": i[0],
                    "iso": self.json_file["state"][i[0]][1],
                    "woeid": self.json_file["state"][i[0]][0],
                    "type": "state"
                })
        for i in self.json_file["country"].items():
            if q.lower() in i[0].lower() and not i[0] in resultsList:
                resultsList.append({
                    "name": i[0],
                    "iso": self.json_file["country"][i[0]][1],
                    "woeid": self.json_file["country"][i[0]][0],
                    "type": "country"
                })

        return resultsList
