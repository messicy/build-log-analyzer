import re
import os
import pprint
import smtplib
from pathlib import Path

bundlePattern = re.compile(r'DisplayProgressbar: Building AssetBundle(?s).*?Completed \'Build.AssetBundle', re.MULTILINE)
staticbundlenamePattern = re.compile(r'(static+.*)\'')
otabundlenamePattern = re.compile(r'(ota+.*)\'')
dynabundlenamePattern = re.compile(r'(dyna+.*)\'')
resourcePattern = re.compile(r'.*%.*/.*')
spritePattern = re.compile(r'.*-fmt.*')
guidPattern = re.compile(r'guid: (.*)')
resInPackagePattern = re.compile(r'BootScene.unity(?s).*?VoronoiRenderer')

matPattern = re.compile(r'(.*\.mat)\n')
shaderPattern = re.compile(r'm_Shader: .*fileID: (.*),')
texturePattern = re.compile(r'm_Texture: .*guid: (.*),')
tintPattern = re.compile(r'name: _TintColor\n.*sec.*{(.*)}')

prefabPattern = re.compile(r'(.*\.prefab)\n')
nodePattern = re.compile(r'- 198: {(?s).*?m_IsActive: .')
nodenamePattern = re.compile(r'm_Name: (.*)\n')
# workingPath = os.getcwd()[:-24] + "Game/"
workingPath = "/Users/messi/Work/KOA/dragon-client-code_ios/Game/"


res2SizeDict = dict()
res2NumDict = dict()
res2BundleDict = dict()
res2SizeSumDict = dict()
res2SizeSumSortedDict = dict()

bundle2ResDict = dict()

filetype = list()

def calsize(ori):
    data = ori.split(' ')
    if data[2] == 'mb':
        return float(data[1]) * 1024
    else:
        return data[1]

defaultRes = [
]

realRes = list()

def analyzePackageInfo(log):
    package = re.findall(resInPackagePattern, log)
    ress = re.findall(resourcePattern, package[0])
    for res in ress:
        if ".cs" in res or ".shader" in res:
            continue

        data = re.split(r'\t.*.[0-9]% ', res)
        resourcename = data[1]
        realRes.append(resourcename)

    logFile = open("result", "a")
    pprint.pprint("1.Analyze resource in Package...", logFile)
    pprint.pprint("what's less", logFile)
    pprint.pprint(list(set(defaultRes) - set(realRes)), logFile)

    pprint.pprint("what's more ", logFile)
    pprint.pprint(list(set(realRes) - set(defaultRes)), logFile)

    pprint.pprint("what's default(exclude cs and shader) ", logFile)
    pprint.pprint(defaultRes, logFile)

matid2matdict = dict()

def analyzeDuplicateMat(log):
    print("\n3.Analyze duplicate material in bundle...", file=open("result", "a"))

    mats = re.findall(matPattern, log)
    for mat in mats:
        data = re.split(r'\t.*.[0-9]% ', mat)
        matname = data[1]
        # print(matname)
        matfilepath = workingPath + matname
        matfile = open(matfilepath, "r")
        if matfile:
            matfilecontent = matfile.read()
            shaders = re.findall(shaderPattern, matfilecontent)
            # print(shaders)
            textures = re.findall(texturePattern, matfilecontent)
            tintcolor = re.findall(tintPattern, matfilecontent)
            if len(tintcolor) == 0:
                tintcolor.append("notintcolor")
            # print(textures)
            if len(textures) == 1:
                matid = shaders[0] + "_" + textures[0] + "_" + tintcolor[0]
                # print(matid)
                if matid in matid2matdict:
                    if matname not in matid2matdict[matid]:
                        matid2matdict[matid].append(matname)
                else:
                    matid2matdict[matid] = list()
                    matid2matdict[matid].append(matname)

    for matid in matid2matdict:
        if len(matid2matdict[matid]) > 1:
            # print("-----------", file=open("result", "a"))
            print(matid, file=open("result", "a"))
            for mat in matid2matdict[matid]:
                print(mat, file=open("result", "a"))

def analyzeInactiveVFXNode(log):
    print("\n4.Analyze inactive node in prefab...", file=open("result", "a"))

    prefabs = re.findall(prefabPattern, log)
    for prefeb in prefabs:
        data = re.split(r'\t.*.[0-9]% ', prefeb)
        prefabname = data[1]
        # print(prefabname)
        prefabfilepath = workingPath + prefabname
        prefabfile = open(prefabfilepath, "r")
        if prefabfile:
            prefabfilecontent = prefabfile.read()
            nodes = re.findall(nodePattern, prefabfilecontent)
            for node in nodes:
                if "m_IsActive: 0" in node:
                    nodename = re.findall(nodenamePattern, node)
                    print(prefabname + " has inactive vfx node " + nodename[0], file=open("result", "a"))


def sendMail():
    SERVER = "smtp.gmail.com"
    FROM = "dragonwarci1@gmail.com"
    TO = ["yue.chen@funplus.com",
          "lihua.ming@funplus.com",
          # "jinquan.xue@funplus.com"
          ]  # must be a list

    SUBJECT = "KOA build analyze"
    TEXT = open("result", "r").read()

    # Prepare actual message
    message = """From: %s\r\nTo: %s\r\nSubject: %s\r\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)

    server = smtplib.SMTP(SERVER, 587)
    server.ehlo()
    server.starttls()
    server.login(FROM, "Dragon_war1")
    server.sendmail(FROM, TO, message)
    server.quit()


if __name__ == '__main__':
    my_file = Path("result")
    if my_file.is_file():
        os.remove("result")

    with open("bundle log", "r") as f:
        log = f.read()
        analyzePackageInfo(log)
        # analyzeBundleInfo(log)
        analyzeDuplicateMat(log)
        analyzeInactiveVFXNode(log)
        sendMail()