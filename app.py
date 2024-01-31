#imports
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
from fuzzywuzzy import fuzz 
from fuzzywuzzy import process 
from typing import Literal

#load environment variables from .env file in same directory, fetch variables using os.get_env('variable')
load_dotenv()

MIN_RATIO = 85

#Literal arrays to use as dropdown options
SortList = Literal[
    'Name',
    'HP',
    'SP',
    'P.Atk',
    'P.Def',
    'E.Atk',
    'E.Def',
    'Crit',
    'Spd'
]        

AttributeList = Literal[
        'Sword',
        'Axe',
        'Bow',
        'Fan',
        'Tome',
        'Dagger',
        'Staff/Stave',
        'Polearm/Spear',
        'Wind',
        'Fire',
        'Ice',
        'Lightning/Thunder',
        'Light',
        'Dark',
        'Heal',
        'Buff',
        'Debuff'
    ]

DisplayList = Literal[
    'Full',
    'Stats',
    'Passive Skills',
    'Battle Skills',
    'Ultimate Technique',
    'Awakening IV Accessory',
    'Art',
    'Story'
]

SkillTypeList = Literal[
    'All',
    'Passive Skills',
    'Battle Skills',
    'Ultimate Technique',
    'Awakening IV Accessory'
]

BuffList = Literal[
    #Buffs
    #Restore
    'HP Heal',
    'HP Regen',
    'Revive',
    'SP Heal',
    'HP Up',
    "BP Restore",
    #Special
    'Cover',
    'Taunt',
    'Damage Reduction',
    'Sidestep',
    'DeadEye',
    'HP Shield',
    'Ult Gauge',
    #Stats
    'P.Atk Up',
    'E.Atk Up',
    'P.Def Up',
    'E.Def Up',
    'Crit Up',
    'Speed Up',
    'Damage Up',
    'Weapon Damage Up',
    #Effects
    'Remove Ailments',
    'Immunity'
]

DebuffList = Literal[
    #Debuffs
    #Stat
    'P.Def Down',
    'E.Def Down',
    'P.Atk Down',
    'E.Atk Down',
    #Magic
    'Fire Res Down',
    'Ice Res Down',
    'Lightning Res Down',
    'Wind Res Down',
    'Light Res Down',
    'Dark Res Down',
    #Weapon
    'Sword Res Down',
    'Axe Res Down',
    'Spear Res Down',
    'Fan Res Down',
    'Bow Res Down',
    'Tome Res Down',
    'Staff Res Down',
    'Dagger Res Down',
    #Effects
    'Paralysis',
    'Poison',
    'Bleed',
    'Combustion',
    'Blindness' ,
    'Taunt',
    'Intimidate'
]
               
#list of discord emoji's, so we can easily convert search values into emoji's
EmojiList = {
    'Sword' : '<:Sword:1197108600653496370>',
    'Axe' : '<:Axe:1197108585969221722>',
    'Bow' : '<:Bow:1197108584220213248>',
    'Spear' : '<:Spear_Polearm:1197108588301254677>',
    'Polearm' : '<:Spear_Polearm:1197108588301254677>',
    'Dagger' : '<:Dagger:1197108587105886250>',
    'Fan' : '<:Fan:1197108579082174505>',
    'Staff' : '<:Staff_Staves:1197108582995460138>',
    'Stave' : '<:Staff_Staves:1197108582995460138>',
    'Tome' : '<:Tome:1197108581577789491>',
    'Wind' : '<:Wind:1197141884959731793>',
    'Ice' : '<:Ice:1197108589681180682>',
    'Fire' : '<:Fire:1197108593443483791>',
    'Lightning' : '<:Lightning_Thunder:1197108596786348093>',
    'Thunder' : '<:Lightning_Thunder:1197108596786348093>',
    'Light': '<:Light:1197108591962882168>',
    'Dark': '<:Dark:1197108677069504602>',
    'Heal': '<:Heal:1198387991186514032>',
    'Buff': '<:Buff:1198387985880727552>',
    'Debuff': '<:Debuff:1198387982651109517>'
}
#create directories if it doesn't exist
isExist = os.path.exists('units')
if not isExist:
    os.makedirs('units')
    
isExist = os.path.exists('pets')
if not isExist:
    os.makedirs('pets')
    
isExist = os.path.exists('divinebeasts')
if not isExist:
    os.makedirs('divinebeasts')
    
isExist = os.path.exists('bosses')
if not isExist:
    os.makedirs('bosses')

#setup a global variable for the messaging functions
needsfollowup = False

#setup the intents, all will fetch all available intents (rather than all intents, it fetches the intents currently available to the bot)
intents = discord.Intents.all()
#we want to get intent to read the message content, though with commansd we might not need it
intents.message_content = True

#small helper class I found somewhere, it's being used by alot of people not source what the original source is.
class aclient(discord.Client):
    def __init__(self):
        #set intents, since this is running async, we put the synced attribute to false on initialization
        super().__init__(intents=discord.Intents.all())
        self.synced = False
    
    async def on_ready(self):
        #wait until ready
        await self.wait_until_ready()
        #if not synced yet, the bot shouldn't come here if it's already synced though, but doesn't hurt being safe, maybe on restart of bot using a command?
        if not self.synced:
            synced = await tree.sync()
            print(f'Synced {len(synced)} commands!')
            self.synced = True
            
        print(f'Logged in as {self.user}!')

#function to help parse for the sort
def ignore_exception(IgnoreException=Exception,DefaultVal=0):
    """ Decorator for ignoring exception from a function
    e.g.   @ignore_exception(DivideByZero)
    e.g.2. ignore_exception(DivideByZero)(Divide)(2/0)
    """
    def dec(function):
        def _dec(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except IgnoreException:
                return DefaultVal
        return _dec
    return dec

sint = ignore_exception(ValueError)(int)

#get a printable string for the embed, this will fit all our skills and also the accessories
def getDescriptionString(dict):
    descr = ''
    for skill in dict:
        info = dict[skill]
        
        for attr in info['Image']:
            descr = descr + attr
            
        descr = descr + '**' + info['Name'].replace('\n', '') + '** ' + info['Description'] + '\n'

    return descr

#get specific display for the stats
def getStatDescriptionString(dict):
    return '**Class**: ' + dict['Class'] + '\n**Attributes**: ' + ("".join(dict['Attributes'])) + '\n**Job**: ' + dict['Job'] + '\n**Influence**: ' + dict['Influence'] + '\n**HP**: ' + dict['HP'] + '\n**SP**: ' + dict['SP'] + '\n**P.Atk**: ' + dict['P.Atk'] + '\n**P.Def**: ' + dict['P.Def'] + '\n**E.Atk**: ' + dict['E.Atk'] + '\n**E.Def**: ' + dict['E.Def'] + '\n**Crit**: ' + dict['Crit'] + '\n**Spd**: ' + dict['Spd']                

#full display function, which is just calling the other functions above
def getFullDescriptionString(dict):
    descr = '### Stats \n' + getStatDescriptionString(dict) + '\n\n'
    descr = descr + '### Passive Skills \n' + getDescriptionString(dict['Passive Skills']) + '\n'
    descr = descr + '### Battle Skills \n' + getDescriptionString(dict['Battle Skills']) + '\n'    
    descr = descr + '### Ultimate Technique \n' + getDescriptionString(dict['Ultimate Technique']) + '\n'    
    descr = descr + '### <:Awakening_IV:1197108701656514590>Awakening IV Accessory\n' + getDescriptionString(dict['Awakening IV Accessory'])    
    return descr

#get description helper function, to determine what kind of content we want to show
def getDescription(dict, display):
    if display == 'Stats':
        return getStatDescriptionString(dict)
    elif display == 'Full':
        return getFullDescriptionString(dict)
    else:
        return getDescriptionString(dict[display])
        
#get description helper function, to determine what kind of content we want to show
def getDBDescription(dict):
    descr = ''
    descr = descr + '### Passive Skills \n' + getDescriptionString(dict['Passive Skills']) + '\n'
    descr = descr + '### Battle Skills \n' + getDescriptionString(dict['Battle Skills']) + '\n'    
    
    return descr
    
#get description helper function, to determine what kind of content we want to show
def getPetDescription(dict):
    descr = '### Stats \n\n**HP**: ' + dict['HP'] + '\n**SP**: ' + dict['SP'] + '\n**P.Atk**: ' + dict['P.Atk'] + '\n**P.Def**: ' + dict['P.Def'] + '\n**E.Atk**: ' + dict['E.Atk'] + '\n**E.Def**: ' + dict['E.Def'] + '\n**Crit**: ' + dict['Crit'] + '\n**Spd**: ' + dict['Spd'] + '\n' 
    descr = descr + '### Battle Skills \n' + getDescriptionString(dict['Battle Skills']) + '\n'    
    
    return descr
    
#send response message to the command received, you can only reply to a command once, hence the need of the followup variable
async def sendReplyMessage(ctx: discord.interactions.Interaction, message):
    global needsfollowup
    if needsfollowup:
        await ctx.followup.send(message)
    else:
        await ctx.response.send_message(message)
    
    needsfollowup = True
    return

#send response message to the command received, you can only reply to a command once, hence the need of the followup variable
async def sendReplyEmbed(ctx: discord.interactions.Interaction, embed):
    global needsfollowup
    if needsfollowup:
        await ctx.followup.send(embed=embed)
    else:
        await ctx.response.send_message(embed=embed)
    
    needsfollowup = True
    return
#reset the global needsfollowup variable
def resetFollowUp():
    global needsfollowup
    needsfollowup = False
    return

def sortUnitList(list, sort):
    if sort == 'Name':
        sortedlist = sorted(list, key=lambda x:x[sort])
    else:
        sortedlist = sorted(list, key=lambda x:sint(x[sort]), reverse=True)
    return sortedlist
 
#search units 
async def processUnitSearch(interaction, type, input, display, sort):
    resetFollowUp()
    #parsing the input, ucfirst
    try:
        input = input[0].upper() + input[1:]
                
    except:
        input = input
                
    #check if we have an exact match on input
    if os.path.isfile(type + '/' + input + '.txt'):
        try:
            f = open(type + '/' + input + '.txt', 'r')
            
            dict = eval(f.read())
            
            if type == 'pets':
                descrstring = getPetDescription(dict)
            elif type == 'divinebeasts':
                descrstring = getDBDescription(dict)
            else:
                descrstring = getDescription(dict, display)
            
            #create the embed, set the content and the title
            embed = discord.Embed(
                description = descrstring,
                title = dict['Name']
            )
                           
            #set image of the embed
            embed.set_thumbnail(url=dict['Image'])

            #send the embed
            await sendReplyEmbed(interaction, embed)
        
            f.close()
        except:
            await sendReplyMessage(interaction, 'Something went wrong...')
            await sendReplyMessage(interaction, 'Please inform Xylon')
            
    else:
        #list all available units
        unitlist = []    
        for unit in os.listdir(type):
            #remove the .txt or .json part of the filename, so we are left with unit names
            unitlist.append(unit.split('.', 1)[0])
        
        #using fuzzywuzzy, we get a list of matching elements from our array, max of 10, output format is {Name, MatchRatio}
        exactmatch = False
        found = process.extract(input, unitlist, limit=10)
        matches = []
        for item in found:
            #since the 2nd element in the response is the Match Ratio we can access it using the [1] element of the object, if it is above the min ratio from our env file, we want to add it to the match array
            if item[1] >= MIN_RATIO:
                #since the 1st element in the response is the name, we can access it using the [0] element of the object, we add it to the matching array
                if exactmatch == False:
                    matches.append(item[0])
                    if item[0].lower() == input.lower():
                        exactmatch = True
            else:
                continue
        
        #no matches are found, too bad
        if len(matches) == 0:
            await sendReplyMessage(interaction, 'No matching ' + type + ' found for "'+ input +'"!')
            return 
        
        #exactly one match is found
        elif len(matches) == 1:
            #try to access the file, if for some reason this isn't possible, something horrible might be going on
            try:
                if os.path.isfile(type + '/' + matches[0] + '.txt'):
                    f = open(type + '/' + matches[0] + '.txt', 'r')
                    #we use eval, to parse it as a json object, in this case a dict {}
                    dict = eval(f.read())
                   
                    if type == 'pets':
                        descrstring = getPetDescription(dict)
                    elif type == 'divinebeasts':
                        descrstring = getDBDescription(dict)
                    else:
                        descrstring = getDescription(dict, display)
           
                    embed = discord.Embed(
                        description = descrstring,
                        title = dict['Name']
                    )
                    
                    embed.set_thumbnail(url=dict['Image'])
                    await sendReplyEmbed(interaction, embed)
                    f.close() 
                
            except:
                await sendReplyMessage(interaction, 'Something went wrong...')
                await sendReplyMessage(interaction, 'Please inform Xylon')
                
            return
            
        else:
            await sendReplyMessage(interaction, 'Found ' + str(len(matches)) + ' matches! {'+", ".join(matches)+'}')
                

            #first get the details of all units found
            fullunitinfolist = []
            for match in matches:
                try:
                    if os.path.isfile(type + '/' + match + '.txt'):
                        f = open(type + '/' + match + '.txt', 'r')

                        dict = eval(f.read())
                        fullunitinfolist.append(dict)
                        f.close()
                except:
                    await sendReplyMessage(interaction, 'Something went wrong...')
                    await sendReplyMessage(interaction, 'Please inform Xylon')
                
            #then sort the list using the input given
            sortedlist = sortUnitList(fullunitinfolist, sort)
            #if we have more than 1 match, we loop over the matches
            for match in sortedlist:
                if type == 'pets':
                    descrstring = getPetDescription(match)
                elif type == 'divinebeasts':
                    descrstring = getDBDescription(match)
                else:
                    descrstring = getDescription(match, display)
            
                embed = discord.Embed(
                    description = descrstring,
                    title = match['Name']
                )

                #send a message for each unit
                embed.set_thumbnail(url=match['Image'])
                await sendReplyEmbed(interaction, embed)

                f.close() 

#return list of units/pets/divine beasts matching the searched skill
def searchUnitSkills(unittype, searchtype, search):
    units = []
    unitlist = os.listdir(unittype)

    #get all matching units
    for unit in unitlist:
        added = False
        f = open(unittype + '/' + unit, 'r')
        unitdata = eval(f.read())
        f.close()

        #try looking for the skill in different lists
        if searchtype == 'All' or searchtype == 'Battle Skills':
            for skillitem in unitdata['Battle Skills']:
                if added == False:
                    if search in unitdata['Battle Skills'][skillitem]['Type']:
                        units.append(unitdata)
                        continue
                else:
                    continue
        
        if searchtype == 'All' or searchtype == 'Passive Skills':
            for skillitem in unitdata['Passive Skills']:
                if added == False:
                    if search in unitdata['Passive Skills'][skillitem]['Type']:
                        units.append(unitdata)
                        continue
                else:
                    continue
        if searchtype == 'All' or searchtype == 'Ultimate Technique':
            for skillitem in unitdata['Ultimate Technique']:
                if added == False:
                    if search in unitdata['Ultimate Technique'][skillitem]['Type']:
                        units.append(unitdata)
                        continue
                else:
                    continue

        if searchtype == 'All' or searchtype == 'Awakening IV Accessory':
            for skillitem in unitdata['Awakening IV Accessory']:
                if added == False:
                    if search in unitdata['Awakening IV Accessory'][skillitem]['Type']:
                        units.append(unitdata)
                        continue
                else:
                    continue
                    
    return units
    
def getUnitList(type):
    fullunitinfolist = []
    for unit in os.listdir(type):
        if os.path.isfile(type + '/' + unit):
            f = open(type + '/' + unit, 'r')

            dict = eval(f.read())
            fullunitinfolist.append(dict)
            f.close()

    return fullunitinfolist
    

#actual code starts here, init the client
client = aclient()
#set the command tree, everything set using the tree decorators will get synced to the command tree
tree = app_commands.CommandTree(client)

#about function
#using @ is called a decorator often used for description purposes
@tree.command(name='about', description='Display a short description text for the bot')
async def self(interaction: discord.interactions.Interaction):
    resetFollowUp()
    await sendReplyMessage(interaction, 'HelloNya my name is Isla and my purrrpose is to provide you with info about units and more!')
    
#help function
@tree.command(name='help', description='Lists the available commands')
async def self(interaction: discord.interactions.Interaction):
    resetFollowUp()
    await sendReplyMessage(interaction, 'Available commands: \n/help\n/about\n/credits\n/unit\n/unitlist\n/attribute\n/attributelist\n/buff\n/debuff\n/pet\n/petlist\n/petbuff\n/petdebuff\n/divinebeast\n/divinebeastlist')
    
#credits function
@tree.command(name='credits', description='Display the credits for this bot')
async def self(interaction: discord.interactions.Interaction):
    resetFollowUp()
    await sendReplyMessage(interaction, 'Bot made by Xylon. \nMonty for the [notion site](https://phrygian-tuesday-3c6.notion.site/2dd50eb0e188493fbecee1f55b8691c2) and providing the initial data. \nMaster Roxas for refining and adding more details to the data.\nCentralCommand for pet and divine beast images and data.\nSpecial credits to game8.jp, Mr. Smokestack, Urshiko, Shizukatz and Finger.')

#unit function
@tree.command(name='unit', description='Display information for a unit, this uses fuzzy search')
async def self(interaction: discord.interactions.Interaction, traveler: str, display:DisplayList='Stats', sort:SortList='Name'):
    await processUnitSearch(interaction, 'units', traveler, display, sort)
                
#pet function
@tree.command(name='pet', description='Display information for a pet, this uses fuzzy search')
async def self(interaction: discord.interactions.Interaction, pet: str, sort:SortList='Name'):
    display = 'Full'
    await processUnitSearch(interaction, 'pets', pet, display, sort)
    
                
#divinebeast function
@tree.command(name='divinebeast', description='Display information for a divine beast, this uses fuzzy search')
async def self(interaction: discord.interactions.Interaction, divinebeast: str):
    sort = 'Name'
    display = 'Full'
    await processUnitSearch(interaction, 'divinebeasts', divinebeast, display, sort)

#get a list of all units    
@tree.command(name='unitlist', description='Display a list of all units')
async def self(interaction: discord.interactions.Interaction, sort:SortList='Name'):
    resetFollowUp()
    unitlist = []    

    sortedlist = sortUnitList(getUnitList('units'), sort)

    for unit in sortedlist:
        unitlist.append(unit['Name'])
    
    #split the list with a newline between each element
    await sendReplyMessage(interaction, "\n".join(unitlist))
    
    
#get a list of all pets    
@tree.command(name='petlist', description='Display a list of all pets')
async def self(interaction: discord.interactions.Interaction, sort:SortList='Name'):
    resetFollowUp()
    petlist = []    

    sortedlist = sortUnitList(getUnitList('pets'), sort)

    for pet in sortedlist:
        petlist.append(pet['Name'])
    
    #split the list with a newline between each element
    await sendReplyMessage(interaction, "\n".join(petlist))
    
#get a list of all pets    
@tree.command(name='divinebeastlist', description='Display a list of all divine beasts')
async def self(interaction: discord.interactions.Interaction):
    resetFollowUp()
    sort = 'Name'
    petlist = []    

    sortedlist = sortUnitList(getUnitList('divinebeasts'), sort)

    for pet in fullpetinfolist:
        petlist.append(pet['Name'])
    
    #split the list with a newline between each element
    await sendReplyMessage(interaction, "\n".join(petlist))

#search using an attribute
@tree.command(name='attribute', description='Search units matching 1 or more attributes, use /attributelist to see all available attributes')
async def self(interaction: discord.interactions.Interaction, attributes: str, sort:SortList='Name'):
    resetFollowUp()
    listofunits = os.listdir('units')
    unitlist = []
    
    try:
        for unit in listofunits:
            f = open('units/' + unit, 'r')
            unitdata = eval(f.read()) 
            unitlist.append(unitdata)
            f.close()
    
    except:
        await sendReplyMessage(interaction, 'Sorry! Error when reading directory and files...') 
    
    #for each searched attribute, we split on a whitespace, so dark fire will result in [dark, fire]
    for attribute in attributes.split():
        #again UCFirst
        try:
            attribute = attribute[0].upper() + attribute[1:]
            
        except:
            attribute = attribute
        
        #if the attribute can be found in the list, we convert it to the emoji value, since that's what's in the array
        if attribute in EmojiList:
            search = EmojiList[attribute]
            
        else:
            await sendReplyMessage(interaction, 'Sorry, but the attribute called ' + attribute + ' could not be recognized!') 
            return
            
        newunitlist = []
        
        #get all matching units
        for unit in unitlist:
            if search in unit['Attributes']:
                newunitlist.append(unit)
            
        #store them in a new list, which is getting used for the second or third etc attributes, so we can keep working with units that matched the previous attribute    
        unitlist = newunitlist
        
    printableunits = []
    sortedlist = sortUnitList(unitlist, sort)

    for unit in sortedlist:
        printableunits.append(unit['Name'])
    
    #if we have any units, we show them, if we don't we show an appropriate message
    if(len(printableunits) > 0):
        await sendReplyMessage(interaction, "\n".join(printableunits))
    else:
        await sendReplyMessage(interaction, 'No units found matching the selected attributes!')

#show a list of all available attributes
@tree.command(name='attributelist', description='Display a list of all available attributes')
async def self(interaction: discord.interactions.Interaction):
    resetFollowUp()
    global EmojiList
    #list all elements, of the Emoji dictionary, since that's the one we use to search
    await sendReplyMessage(interaction, "\n".join(EmojiList.keys())) 

#show  units based on input buff
@tree.command(name='buff', description='Find units which have a certain skill')
async def self(interaction: discord.interactions.Interaction, skill:BuffList, skilltype: SkillTypeList='All', sort:SortList='Name'):
    resetFollowUp()
    
    sortedlist = sortUnitList(searchUnitSkills('units', skilltype, skill), sort)

    printableunits = []
    for unit in sortedlist:
        printableunits.append(unit['Name'])

    #if we have any units, we show them, if we don't we show an appropriate message
    if(len(printableunits) > 0):
        await sendReplyMessage(interaction, "\n".join(printableunits))
    else:
        await sendReplyMessage(interaction, 'No units found matching the selected skill!')
    
#show  units based on input debuff
@tree.command(name='debuff', description='Find units which have a certain skill')
async def self(interaction: discord.interactions.Interaction, skill:DebuffList, skilltype: SkillTypeList='All', sort:SortList='Name'):
    resetFollowUp()
    
    sortedlist = sortUnitList(searchUnitSkills('units', skilltype, skill), sort)

    printableunits = []
    for unit in sortedlist:
        printableunits.append(unit['Name'])

    #if we have any units, we show them, if we don't we show an appropriate message
    if(len(printableunits) > 0):
        await sendReplyMessage(interaction, "\n".join(printableunits))
    else:
        await sendReplyMessage(interaction, 'No units found matching the selected skill!')
        
#show  pets based on input buff
@tree.command(name='petbuff', description='Find pets which have a certain skill')
async def self(interaction: discord.interactions.Interaction, skill:BuffList, sort:SortList='Name'):
    skilltype = 'Battle Skills'
    resetFollowUp()
   
    sortedlist = sortUnitList(searchUnitSkills('pets', skilltype, skill), sort)

    printableunits = []
    for unit in sortedlist:
        printableunits.append(unit['Name'])

    #if we have any pets, we show them, if we don't we show an appropriate message
    if(len(printableunits) > 0):
        await sendReplyMessage(interaction, "\n".join(printableunits))
    else:
        await sendReplyMessage(interaction, 'No pets found matching the selected skill!')
    
#show  pets based on input debuff
@tree.command(name='petdebuff', description='Find pets which have a certain skill')
async def self(interaction: discord.interactions.Interaction, skill:DebuffList, sort:SortList='Name'):
    skilltype = 'Battle Skills'
    resetFollowUp()
 
    sortedlist = sortUnitList(searchUnitSkills('pets', skilltype, skill), sort)

    printableunits = []
    for unit in sortedlist:
        printableunits.append(unit['Name'])

    #if we have any pets, we show them, if we don't we show an appropriate message
    if(len(printableunits) > 0):
        await sendReplyMessage(interaction, "\n".join(printableunits))
    else:
        await sendReplyMessage(interaction, 'No pets found matching the selected skill!')
        
#start the bot, using the BOT TOKEN we get from the .env file, this is the token you get from the https://discord.com/developers/applications/ page for the bot you want to add
client.run(os.getenv('BOT_TOKEN'))
