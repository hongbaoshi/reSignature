#coding:utf-8
import zipfile,plistlib,sys,re,os,subprocess,datetime
import shutil,getpass

# dev证书名称
dev_p12Name = ''
dev_DEVELOPMENT_TEAM = ''
dev_PRODUCT_BUNDLE_IDENTIFIER = ''
dev_PROVISIONING_PROFILE = ''
dev_PROVISIONING_PROFILE_SPECIFIER =''
dev_aps_environment = ''

# 重新打包
def reZipIpa():
    #删除__MACOSX临时文件
    deleteUselessFiles('__MACOSX')
    ipaPackageName = dev_PRODUCT_BUNDLE_IDENTIFIER
    if ipaPackageName != 0:     
        formt_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        resignIpaName =  ipaPackageName+'_'+ formt_time + '.ipa'
        rezipCmd = 'zip -r ' + resignIpaName + ' Payload'
        process = subprocess.Popen(rezipCmd, shell=True)
        process.wait()
        # 删除Payload文件
        deleteUselessFiles('Payload')
        deleteUselessFiles('__pycache__')
    else:
        formt_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        resignIpaName =  'meitian'+'_'+ formt_time + '.ipa'
        rezipCmd = 'zip -r ' + resignIpaName + ' Payload'
        process = subprocess.Popen(rezipCmd, shell=True)
        process.wait()
        # 删除Payload文件
        deleteUselessFiles('Payload')
        deleteUselessFiles('__pycache__')


#签名
def codesign(certifierName,eplistPath,signPath):
    certifierName = certifierName.lstrip()
    # 重新签名 codesign -f -s $certifierName  --entitlements entitlements.plist Payload/test.app
    signCmd = 'codesign -f -s "' +  certifierName  + '" --entitlements ' + eplistPath + ' ' + signPath
    process = subprocess.Popen(signCmd, shell=True)
    process.wait()



def changeSomeParameter(plist_file,InfoPlist_file):
    print('--------------- 修改工程相关参数')
    if os.path.exists(plist_file):
        readPlists = plistlib.readPlist(plist_file)
        bundleIdentifier = readPlists['channelCFBundleIdentifier']
        bundleDisplayName = readPlists['channelCFBundleDisplayName']
        bundleShortVersion = readPlists['channelCFBundleShortVersionString']
        bundleVersion = readPlists['channelCFBundleVersion']
        if len(bundleIdentifier) > 0:
            changePlistinfo(InfoPlist_file,'CFBundleIdentifier',bundleIdentifier)
        else:
            print('不需要修改包id')

        if len(bundleDisplayName) > 0:
            changePlistinfo(InfoPlist_file,'CFBundleDisplayName',bundleDisplayName)
        else:
            print('不需要修改包名称')

        if len(bundleShortVersion) > 0:
            changePlistinfo(InfoPlist_file,'CFBundleShortVersionString',bundleShortVersion)
        else:
            print('不需要修改包版本')

        if len(bundleVersion) > 0:
            changePlistinfo(InfoPlist_file,'CFBundleVersion',bundleVersion)
        else:
            print('不需要修改包bundle版本')
    else:
        print('-----------------------------  不需要修改工程参数')
    print('------------ 参数修改完成\n\n')

#修改plist文件里的数据
#plist_file 文件路径
#change_name  需要修改的键
#change_value 需要修改的值
def changePlistinfo(plist_file,change_name,change_value):
    if os.path.exists(plist_file):
        #读取plist文件里的数据    
        readPlists = plistlib.readPlist(plist_file)
        readPlists[change_name] = change_value
        plistlib.writePlist(readPlists,plist_file) 
    else:
        print(plist_file + '路径不存在')

def deletePlistKey(plist_file,delete_name):
    if os.path.exists(plist_file):
        #读取plist文件里的数据    
        readPlists = plistlib.readPlist(plist_file)
        del readPlists[delete_name]
        plistlib.writePlist(readPlists,plist_file) 
    else:
        print(plist_file + '路径不存在')




#修改entitlements的内容
def changeEntitlementsPlistinfo():
    application_identifier = dev_DEVELOPMENT_TEAM + '.' + dev_PRODUCT_BUNDLE_IDENTIFIER
    changePlistinfo('entitlements.plist','application-identifier',application_identifier)

    com_apple_developer_team_identifier = dev_DEVELOPMENT_TEAM
    changePlistinfo('entitlements.plist','com.apple.developer.team-identifier',com_apple_developer_team_identifier)

    keychain_access_roups = dev_DEVELOPMENT_TEAM + '.*'
    keychain_access_roups_array = (keychain_access_roups)
    changePlistinfo('entitlements.plist','keychain-access-groups',keychain_access_roups_array)

    if dev_aps_environment:
        changePlistinfo('entitlements.plist','aps-environment',dev_aps_environment)
    else:
        print('不存在dev_aps_environment这个值')
        #删除这个键值
        deletePlistKey('entitlements.plist','aps-environment')


    
# 判断文件是否存在某个字符串
def isExistString(file_path,isString):
    fo = open(file_path,'r')
    for line in fo.readlines():
        if isString in line:
            return True
    return False



# 打开描述文件，读取相应参数
def getParsFromMobile(mobile_path):
    global dev_DEVELOPMENT_TEAM
    global dev_PRODUCT_BUNDLE_IDENTIFIER
    global dev_PROVISIONING_PROFILE
    global dev_PROVISIONING_PROFILE_SPECIFIER
    global dev_aps_environment
    print('从描述文件读取参数...')
    current_path = os.path.abspath(os.path.split(__file__)[0])
    dev_mobilePath = mobile_path
    p = subprocess.call('openssl smime -in %s -inform der -verify >tmp_provisionProfile'%(dev_mobilePath),shell=True)
    if p == 0:
        p = subprocess.check_output("/usr/libexec/PlistBuddy -c 'print TeamIdentifier:0' tmp_provisionProfile",shell=True)
        dev_DEVELOPMENT_TEAM = str(p,encoding='utf-8')
        dev_DEVELOPMENT_TEAM = dev_DEVELOPMENT_TEAM.rstrip('\n')
        p = subprocess.check_output("/usr/libexec/PlistBuddy -c 'print Entitlements:application-identifier' tmp_provisionProfile",shell=True)
        dev_PRODUCT_BUNDLE_IDENTIFIER  = str(p,encoding='utf-8')
        dev_PRODUCT_BUNDLE_IDENTIFIER = dev_PRODUCT_BUNDLE_IDENTIFIER.replace(dev_DEVELOPMENT_TEAM+'.','',1)
        dev_PRODUCT_BUNDLE_IDENTIFIER = dev_PRODUCT_BUNDLE_IDENTIFIER.rstrip('\n')
        p = subprocess.check_output("/usr/libexec/PlistBuddy -c 'print UUID' tmp_provisionProfile",shell=True)
        dev_PROVISIONING_PROFILE = str(p,encoding='utf-8')
        dev_PROVISIONING_PROFILE = dev_PROVISIONING_PROFILE.rstrip('\n')
        if isExistString(current_path+'/tmp_provisionProfile','Name'):
            p = subprocess.check_output("/usr/libexec/PlistBuddy -c 'print Name' tmp_provisionProfile",shell=True)
            dev_PROVISIONING_PROFILE_SPECIFIER = str(p,encoding='utf-8')
            dev_PROVISIONING_PROFILE_SPECIFIER = dev_PROVISIONING_PROFILE_SPECIFIER.rstrip('\n')
        if isExistString(current_path+'/tmp_provisionProfile','aps-environment'):
            p = subprocess.check_output("/usr/libexec/PlistBuddy -c 'print Entitlements:aps-environment' tmp_provisionProfile",shell=True)
            dev_aps_environment = str(p,encoding='utf-8')
            dev_aps_environment = dev_aps_environment.rstrip('\n')
        else:
            dev_aps_environment = ''
        
        print(dev_DEVELOPMENT_TEAM,dev_PRODUCT_BUNDLE_IDENTIFIER,dev_PROVISIONING_PROFILE,dev_PROVISIONING_PROFILE_SPECIFIER,dev_aps_environment)
        
    # 如果不存在描述文件，就导入
    if not os.path.exists('/Users/%s/Library/MobileDevice/Provisioning Profiles/%s.mobileprovision'%(getpass.getuser(),dev_PROVISIONING_PROFILE)):
        os.system('open %s'%(dev_mobilePath))
    # 删除mobile临时文件
    os.remove(os.getcwd()+'/tmp_provisionProfile')
    print('描述文件参数读取完成\n\n')



def getP12Name(cer_path,cer_password):
    global dev_p12Name
    print('开始获取p12证书的名称...')
    
    devP12Path = cer_path
    devP12Password = cer_password
    p = subprocess.call('security import %s -k ~/Library/Keychains/login.keychain -P %s -T /usr/bin/codesign'%(devP12Path,devP12Password),shell=True)
    if p == 0:
        p = subprocess.check_output('openssl pkcs12 -nodes -in %s -info -nokeys -passin "pass:%s" 2>/dev/null | grep "friendlyName"'%(devP12Path,devP12Password),shell=True)
        p= str(p,encoding='utf-8')
        p= p.strip()
        p= p.replace('friendlyName:','',1)
        p = p.rstrip('\n')
        dev_p12Name = p

    print('dev证书名称:',dev_p12Name)
    if len(dev_p12Name)<10:
        print('\n ----------------------- 证书名称读取失败，终止程序，手动输入证书名称 -----------------------\n')
        print('\n\n')

        message = ''
        message = input("请输入改证书的名称(如：iPhone Developer: Chen Lili (MV7Y75X353))：")
        if len(message)>9:
            dev_p12Name = message
        else:
            print('请输入正确的证书名称\n\n')
            exit()
    print('获取证书名称结束\n\n')




#获取*.app的绝对路径
def getAppPath():
  
    PayloadPath = os.getcwd() + '/Payload'

    deleteUselessFiles(PayloadPath + '/.DS_Store')

    appPaths = os.listdir(PayloadPath)
    
    for appPath in appPaths:
        if '.app' in appPath:
            return PayloadPath + '/' + appPath
    return null

#删除无用的文件
def deleteUselessFiles(name):
    delCmd = 'rm -rf ' + name
    process = subprocess.Popen(delCmd, shell=True)
    process.wait()

#复制文件到某目录
def cpFiles(oldPath,newName):
    cpCmd = 'cp ' + oldPath + ' ' + newName
    process = subprocess.Popen(cpCmd, shell=True)
    process.wait()

#解压
def unzipIpa(ipaPath):
    zipName = 'resign.zip'
    # 复制成.zip后缀
    cpFiles(ipaPath,zipName)

    # 解压zip到指定目录
    unzipCmd = 'unzip  -o ' + zipName
    process = subprocess.Popen(unzipCmd, shell=True)
    process.wait()

    #删除无用的zip文件
    deleteUselessFiles(zipName)




#重签名流程
def resign(ipa_path,cer_path,cer_password,mobile_path):
    global dev_p12Name
    print('---------------------- 开始重签名')
    #解压ipa包
    unzipIpa(ipa_path)
    # exit()

    #获取.app的绝对路径
    appPath = getAppPath()

    #删除Payload/*.app/_CodeSignature,删除签名文件
    deleteUselessFiles(appPath + '/_CodeSignature')

    #替换证书配置文件Payload/*.app/embedded.mobileprovision，替换描述文件
    cpFiles(mobile_path,appPath + '/embedded.mobileprovision')

    #从证书读取证书名字
    getP12Name(cer_path,cer_password)

    #从描述文件读取entitlements.plist相关信息
    getParsFromMobile(mobile_path)

    #修改entitlements.plist的内容
    changeEntitlementsPlistinfo()
    # message = input("骚等......")


    #判断是否需要修改游戏名称、bundleid、游戏Version、游戏build version -------- 这四个值默认为空，不修改
    changeSomeParameter('parameter.plist',appPath+'/Info.plist')


    #给动态库重签名,
    #这个地方需要判断是否存在动态库
    current_path = os.path.abspath(os.path.split(__file__)[0])
    if os.path.exists(appPath + '/Frameworks'):
        frameworksPath = os.listdir(appPath + '/Frameworks')
        for frameworkPath in frameworksPath:
             # 给Frameworks签名
            codesign(dev_p12Name,current_path+'/entitlements.plist',appPath + '/Frameworks' +'/'+ frameworkPath)
    else:
        print('------------------- 没有需要重签的动态库')

    #给.app重签名
    codesign(dev_p12Name,current_path+'/entitlements.plist',appPath)

    #打成ipa包
    reZipIpa()

    print('---------------------- 重签名结束')



if  __name__ == '__main__':

    # print(os.path.abspath(os.path.split(__file__)[0]))
    # exit()

    #ipa路径
    ipa_path = sys.argv[1]

    #证书路径
    cer_path = sys.argv[2]

    #证书密码
    cer_password = sys.argv[3]

    #mobileprovision文件路径
    mobile_path = sys.argv[4]

    #重签名打包
    resign(ipa_path,cer_path,cer_password,mobile_path)













































