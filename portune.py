# -*- coding: utf-8 -*-
#from nonebot import MessageSegment
import random
import os
import hoshino
from hoshino.util import DailyNumberLimiter
from hoshino import R, Service
from hoshino.util import pic2b64
from hoshino.typing import *
from .pcr.luck_desc import luck_desc as luck_desc1
from .luck_type import luck_type
from .df.luck_desc import luck_desc as luck_desc2
from .genshin.luck_desc import luck_desc as luck_desc3
from .uma.luck_desc import luck_desc as luck_desc4
from PIL import Image, ImageDraw, ImageFont
import configparser
from .grouputils import *



descDict = {'pcr':luck_desc1,'th':luck_desc2,'genshin':luck_desc3,'uma':luck_desc4}
luck_desc_list = [luck_desc1,luck_desc2,luck_desc3,luck_desc4]

sv_help = '''
[抽签|人品|运势|抽凯露签]
随机角色/指定凯露预测今日运势
准确率高达114.514%！
'''.strip()
#帮助文本
sv = Service('portune', help_=sv_help, bundle='pcr娱乐')

lmt = DailyNumberLimiter(1)
#设置每日抽签的次数，默认为1
Data_Path = hoshino.config.RES_DIR

#获取底图存放路径
def get_img_path(desc):
    if desc == luck_desc1:
        Img_Path = 'portunedata/imgbase/pcr'
    elif desc == luck_desc2:
        Img_Path = 'portunedata/imgbase/df'
        #th=touhou=东方=df
    elif desc == luck_desc3:
        Img_Path = 'portunedata/imgbase/genshin'
    elif desc == luck_desc4:
        Img_Path = 'portunedata/imgbase/uma'
    return Img_Path

@sv.on_prefix(('portune启用'))
async def portuneEnable(bot, ev):
    rawMessage = ev.raw_message
    content=rawMessage.split()
    enabledPkg = getEnabledPackage(ev.group_id)
    if content[1] in enabledPkg:
        msg = '此包已经启用过了'
    elif content[1] in allPkgs:
        enabledPkg.append(content[1])
        enabledPkgTxt = ''
        for i in enabledPkg:
            enabledPkgTxt = enabledPkgTxt + i + ','
        #config=configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
        config.set(str(ev.group_id),'enabled',enabledPkgTxt)
        config.write(open(os.path.join(os.path.dirname(__file__), "config.ini"), "w"))
        msg = f'已启用{content[1]},当前已启用的包：{enabledPkgTxt}'
    else:
        msg = '您要启用的包名不存在或者输入不合法，请注意指令与参数之间需要空格'
    await bot.send(ev,msg) 

@sv.on_prefix(('portune禁用'))
async def portuneDisable(bot, ev):
    rawMessage = ev.raw_message
    content=rawMessage.split()
    enabledPkg = getEnabledPackage(ev.group_id)
    if content[1] in enabledPkg:
        enabledPkg.remove(content[1])
        msg = f'已禁用包{content[1]}'
        enabledPkgTxt = ''
        for i in enabledPkg:
            enabledPkgTxt = enabledPkgTxt + i + ','
        #config=configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
        config.set(str(ev.group_id),'enabled',enabledPkgTxt)
        config.write(open(os.path.join(os.path.dirname(__file__), "config.ini"), "w"))
    elif content[1] in allPkgs:
        msg = f'此包未启用'
    else:
        msg = '您要禁用的包名不存在或者输入不合法，请注意指令与参数之间需要空格'
    await bot.send(ev,msg) 

@sv.on_fullmatch(('portunels'))
async def portunels(bot, ev):
    #config=configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
    msg = config.get(str(ev.group_id),'enabled')
    if msg == '':
        msg = '没有启用的包，或者未初始化'
    else:
        msg = '当前启用的包：'+msg
    msg += f'\n所有可用的包：{allPkgs}'
    await bot.send(ev,msg) 

@sv.on_prefix(('运势','抽签'), only_to_me=False)
async def portune(bot, ev):
    if not checkIfGroupExists(ev.group_id):
        addGroupSection(ev.group_id)
    uid = ev.user_id
    if not lmt.check(uid):
        await bot.finish(ev, f'你今天已经抽过签了，欢迎明天再来~', at_sender=True)
    lmt.increase(uid)
    pic = drawing_pic(ev.group_id)
    await bot.send(ev, pic, at_sender=True)

def drawing_pic(gid) -> Image:
    fontPath = {
        'title': R.img('portunedata/font/Mamelon.otf').path,
        'text': R.img('portunedata/font/sakura.ttf').path
    }

    enabledPkgs = getEnabledPackage(gid)
    enabledDescList = []
    for pkg in enabledPkgs:
        enabledDescList.append(descDict[pkg])

    luck_desc = random.choice(enabledDescList)
    base_img = random_Basemap(luck_desc)

    filename = os.path.basename(base_img.path)
    charaid = filename.lstrip('frame_')
    charaid = charaid[:-4]

    img = base_img.open()
    # Draw title
    draw = ImageDraw.Draw(img)
    text, title = get_info(charaid,luck_desc)

    text = text['content']
    font_size = 45
    color = '#F5F5F5'
    image_font_center = (140, 99)
    ttfront = ImageFont.truetype(fontPath['title'], font_size)
    font_length = ttfront.getsize(title)
    draw.text((image_font_center[0]-font_length[0]/2, image_font_center[1]-font_length[1]/2),
                title, fill=color,font=ttfront)
    # Text rendering
    font_size = 25
    color = '#323232'
    image_font_center = [140, 297]
    ttfront = ImageFont.truetype(fontPath['text'], font_size)
    result = decrement(text)
    if not result[0]:
        return Exception('Unknown error in daily luck') 
    textVertical = []
    for i in range(0, result[0]):
        font_height = len(result[i + 1]) * (font_size + 4)
        textVertical = vertical(result[i + 1])
        x = int(image_font_center[0] + (result[0] - 2) * font_size / 2 + 
                (result[0] - 1) * 4 - i * (font_size + 4))
        y = int(image_font_center[1] - font_height / 2)
        draw.text((x, y), textVertical, fill = color, font = ttfront)

    img = pic2b64(img)
    img = MessageSegment.image(img)
    return img

def random_Basemap(desc) -> R.ResImg:
    Img_Path = get_img_path(desc)
    base_dir = R.img(Img_Path).path
    random_img = random.choice(os.listdir(base_dir))
    return R.img(os.path.join(Img_Path, random_img))

def get_info(charaid,luck_desc):
    for i in luck_desc:
        if charaid in i['charaid']:
            typewords = i['type']
            desc = random.choice(typewords)
            return desc, get_luck_type(desc)
    raise Exception('luck description not found')

def get_luck_type(desc):
    target_luck_type = desc['good-luck']
    for i in luck_type:
        if i['good-luck'] == target_luck_type:
            return i['name']
    raise Exception('luck type not found')

def decrement(text):
    length = len(text)
    result = []
    cardinality = 9
    if length > 4 * cardinality:
        return [False]
    numberOfSlices = 1
    while length > cardinality:
        numberOfSlices += 1
        length -= cardinality
    result.append(numberOfSlices)
    # Optimize for two columns
    space = ' '
    length = len(text)
    if numberOfSlices == 2:
        if length % 2 == 0:
            # even
            fillIn = space * int(9 - length / 2)
            return [numberOfSlices, text[:int(length / 2)] + fillIn, fillIn + text[int(length / 2):]]
        else:
            # odd number
            fillIn = space * int(9 - (length + 1) / 2)
            return [numberOfSlices, text[:int((length + 1) / 2)] + fillIn,
                                    fillIn + space + text[int((length + 1) / 2):]]
    for i in range(0, numberOfSlices):
        if i == numberOfSlices - 1 or numberOfSlices == 1:
            result.append(text[i * cardinality:])
        else:
            result.append(text[i * cardinality:(i + 1) * cardinality])
    return result

def vertical(str):
    list = []
    for s in str:
        list.append(s)
    return '\n'.join(list)

