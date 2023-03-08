import xml.etree.ElementTree as ET
import os


class SBSDependency:
    def __init__(self, aUrl = '', aFileAbsPath = '', aUID = '', aType = '', aFileUID = '', aVersionUID = ''):
        self.mUrl = aUrl
        self.mFileAbsPath = aFileAbsPath
        self.mUID = aUID
        self.mType = aType
        self.mFileUID = aFileUID
        self.mVersionUID = aVersionUID

    def isHimself(self):
        return self.mUrl == '?himself'


class SBSResource:
    def __init__(self,
                 aIdentifier = '',
                 aUID = '',
                 aType = '',
                 aFormat = '',
                 aCookedFormat = '',
                 aCookedQuality = '',
                 aFilePath = '',
                 aFileAbsPath = '',
                 aLastModif = '',
                 aChecksum = '',
                 aAttributeList = []):
        self.mIdentifier = aIdentifier
        self.mUID = aUID
        self.mType = aType
        self.mFormat = aFormat
        self.mCookerFormat = aCookedFormat
        self.mCookedQuality = aCookedQuality
        self.mFilePath = aFilePath
        self.mFileAbsPath = aFileAbsPath
        self.mLastModif = aLastModif
        self.mChecksum = aChecksum
        self.mAttributeList = aAttributeList


class UrlAliasMgr:
    """
    Class that contains Url Aliases information
    """
    def __init__(self):
        self.mUrlDict = {} # {Name: AbsPath}

    def setAliasAbsPath(self, aAliasName, aAbsPath):
        self.mUrlDict[aAliasName] = aAbsPath

    def getAliasAbsPath(self, aAliasName):
        if not aAliasName in self.mUrlDict:
            return None
        return self.mUrlDict[aAliasName]

    def toAbsPath(self, aUrl):
        for aliasName in self.mUrlDict:
            urlPrefix = aliasName + '://'
            if not aUrl.startswith(urlPrefix):
                continue
            aliasPath = self.mUrlDict[aliasName]
            absPath = aliasPath
            if not absPath.endswith('/'):
                absPath += '/'
            absPath += aUrl[len(urlPrefix):]
            return absPath
        return aUrl


class Context:
    def __init__(self):
        self.mUrlAliasMgr = UrlAliasMgr()
        self.mProgressIndex = 0
        self.mProgressCount = 0

    def getUrlAliasMgr(self):
        return self.mUrlAliasMgr

    def setProgress(self, aIndex, aCount):
        try:
            self.mProgressIndex = int(aIndex)
            self.mProgressCount = int(aCount)
        except:
            self.mProgressIndex = 0
            self.mProgressCount = 0

    def getProgressIndex(self):
        return self.mProgressIndex

    def getProgressCount(self):
        return self.mProgressCount


class SBSDocument:
    def __init__(self, aContext, aFileAbsPath):
        self.mContext = aContext
        self.mFileAbsPath = aFileAbsPath
        self.mSBSDependencyList = []
        self.mSBSResourceList = []
        self.mMetaData = {}

    def parse(self):
        aXmlRoot = None
        try:
            tree = ET.parse(self.mFileAbsPath)
            aXmlRoot = tree.getroot()
            if aXmlRoot is None:
                return False
        except:
            print('Fail to parse xml file "'+str(self.mFileAbsPath)+'"')
            return False

        if not self.__isValidSBS(aXmlRoot):
            return False

        self.mSBSDependencyList = self.__buildSBSDependencyList(aXmlRoot)
        self.mSBSResourceList = self.__buildSBSResourceList(aXmlRoot)
        self.mMetaData = self.__getAllXmlElementsUnder(aXmlRoot, 'metadata')[0]
        return True

    def getSBSDependencyList(self):
        return self.mSBSDependencyList

    def getSBSResourceList(self):
        return self.mSBSResourceList

    def getSBSMetaData(self):
        pass

    def setSBSMetaData(self, aMetaData):
        #self.__setAllXmlElementsUnder('metadata', tree)
        pass

    #==========================================================================
    # Private
    #==========================================================================
    def __getSBSFileDirAbsPath(self):
        return os.path.abspath(os.path.split(self.mFileAbsPath)[0])

    def __toAbsolutePath(self, sbsFileRelativePath):
        absPath = self.mContext.getUrlAliasMgr().toAbsPath(sbsFileRelativePath)
        if absPath == sbsFileRelativePath:
            # File not converted to absPath
            if not os.path.isabs(absPath):
                # Convert to abs path from the current file
                absPath = os.path.abspath(os.path.join(self.__getSBSFileDirAbsPath(), absPath))
        return absPath

    def __buildSBSDependencyList(self, aXmlRoot):
        deps = []
        if aXmlRoot is None:
            return deps
        xmlElmtDependencies = aXmlRoot.find('dependencies')
        if xmlElmtDependencies is None:
            return deps
        for xmlElmtDep in xmlElmtDependencies:
            url = self.__getXmlElementVAttribValue(xmlElmtDep, 'filename')
            fileAbsPath = self.__toAbsolutePath(url)
            dep = SBSDependency(
                aUrl = url,
                aFileAbsPath = fileAbsPath,
                aUID = self.__getXmlElementVAttribValue(xmlElmtDep, 'uid'),
                aType = self.__getXmlElementVAttribValue(xmlElmtDep, 'type'),
                aFileUID = self.__getXmlElementVAttribValue(xmlElmtDep, 'fileUID'),
                aVersionUID = self.__getXmlElementVAttribValue(xmlElmtDep, 'versionUID'))
            if dep.isHimself():
                continue
            deps.append(dep)
        return deps

    def __buildSBSResourceList(self, aXmlRoot):
        sbsResourceList = []
        if aXmlRoot is None:
            return sbsResourceList
        xmlElmtResourceList = self.__getAllXmlElementsUnder(aXmlRoot, 'resource')
        if xmlElmtResourceList is None:
            return sbsResourceList

        for xmlElmtResource in xmlElmtResourceList:
            aAttributeList = []
            filePath = ''
            xmlElmtSourceList = self.__getAllXmlElementsUnder(xmlElmtResource, 'source')
            if xmlElmtSourceList and len(xmlElmtSourceList) > 0:
                xmlElmtExternalCopyList = self.__getAllXmlElementsUnder(xmlElmtSourceList[0], 'externalcopy')
                if xmlElmtExternalCopyList and len(xmlElmtExternalCopyList) > 0:
                    filePath = self.__getXmlElementVAttribValue(xmlElmtExternalCopyList[0], 'filename')

            if len(filePath) == 0:
                filePath = self.__getXmlElementVAttribValue(xmlElmtResource, 'filepath')

            fileAbsPath = self.__toAbsolutePath(filePath)
            sbsResource = SBSResource(
                aIdentifier = self.__getXmlElementVAttribValue(xmlElmtResource, 'identifier'),
                aUID = self.__getXmlElementVAttribValue(xmlElmtResource, 'uid'),
                aType = self.__getXmlElementVAttribValue(xmlElmtResource, 'type'),
                aFormat = self.__getXmlElementVAttribValue(xmlElmtResource, 'format'),
                aCookedFormat = self.__getXmlElementVAttribValue(xmlElmtResource, 'cookedFormat'),
                aCookedQuality = self.__getXmlElementVAttribValue(xmlElmtResource, 'cookedQuality'),
                aFilePath = filePath,
                aFileAbsPath = fileAbsPath,
                aLastModif = self.__getXmlElementVAttribValue(xmlElmtResource, 'lastModif'),
                aChecksum = self.__getXmlElementVAttribValue(xmlElmtResource, 'checksum'))
            sbsResourceList.append(sbsResource)
        return sbsResourceList

    def __getAllXmlElementsUnder(self, aXmlElement, aTagName):
        children = []
        for xmlElmtChild in aXmlElement:
            if xmlElmtChild.tag == aTagName:
                children.append(xmlElmtChild)
            children += self.__getAllXmlElementsUnder(xmlElmtChild, aTagName)

        return children

    def __setAllXmlElementsUnder(self, aTagName, aNewValue):
        tree = ET.parse(self.mFileAbsPath)
        aXmlRoot = tree.getroot()
        aXmlElement = self.__getAllXmlElementsUnder(aXmlRoot, aTagName)

        for xmlElmtChild in aXmlElement:
            aXmlRoot.remove(xmlElmtChild)
        aXmlRoot.insert(1, aNewValue)

        tree.write(self.mFileAbsPath)
        

    def __getXmlElementAttribValue(self, aXmlElement, aAttributeName):
        if aXmlElement is None:
            return None
        return aXmlElement.get(aAttributeName)

    def __getXmlElementVAttribValue(self, aXmlElementParent, aChildName):
        if aXmlElementParent is None:
            return None
        child = aXmlElementParent.find(aChildName)
        if child is None:
            return None
        return self.__getXmlElementAttribValue(child, 'v')

    def __isValidSBS(self, aXmlRoot):
        if aXmlRoot is None:
            return False
        if not aXmlRoot.tag == "package":
            return False
        #pkgTypeElmt = aXmlRoot.find('packageType')
        #if pkgTypeElmt is None:
        #    return False
        #if not self.__getXmlElementAttribValue(pkgTypeElmt, 'v') == 'ProFX':
        #    return False

        return True
