import json
import uuid
import string
import hashlib # sha256
import time
import math
import pyotp
import os
from dotenv import load_dotenv
import copy

import GH2DataRepo

load_dotenv()
adminTOTP = pyotp.TOTP(os.getenv("AdminTOTPCode"))

accounts: dict = None
tokens: dict = None

"""
Token Structure (key is the token)
{
    "UUID": str (UUID of the User it belongs to)
    "Token: str
}
"""

def createAccountSkeleton(
        username: str="", password: str="", uuid: str="", email: str="", isBanned: bool=False, isAdmin: bool=False, creationEpoch: int=0, pfp: str="",
        money: int=0, gameData: dict={}, transactionHistory: list=[], OwnedItems: list=[], TotalXP: int=0, AllSeasonsXP: dict={}
    ) -> dict:
    """
    Account Structure (key is the UUID)
    {
        "Username": str
        "Password": str (sha256 hashed twice)
        "UUID": str
        "Email": str (optional)
        "ProfilePicture": str (url to image)
        "IsBanned": bool
        "IsAdmin": bool
        "CreationEpoch": int (or float)
        "EconomyData": {
            "Money": int
            "GameData": dict(str, dict) (GameName, AnyDataTheyWant) (any data a game wants to store)
            "TransactionHistory": list(str) (A list of strings telling us the history of the user's transactions)
            "OwnedItems": list (A List of all items they own)
            "TotalXP": 0 (Level should be calculable based on the XP number)
            "AllSeasonsXP": {} (Key is the season id/number/name, and the value is how much XP they earned that season!)
        }
    }
    """
    
    return {
        "Username": username,
        "Password": password,
        "UUID": uuid,
        "Email": email,
        "ProfilePicture": pfp,
        "IsBanned": isBanned,
        "IsAdmin": isAdmin,
        "CreationEpoch": creationEpoch,
        "EconomyData": {
            "Money": money,
            "GameData": gameData,
            "TransactionHistory": transactionHistory,
            "OwnedItems": OwnedItems,
            "TotalXP": TotalXP,
            "AllSeasonsXP": AllSeasonsXP
        }
    }


def isUsernameTaken(username: str) -> bool:
    global accounts
    accountValues = accounts.values()
    for account in accountValues:
        if account["Username"] == username: return True
    
    return False

def isUsernameValid(username: str) -> bool:
    if len(username) >= 3 and len(username) <= 16: pass
    else: return False # Length out of range
    
    validCharacters = string.ascii_letters + string.digits + "_"
    for char in username:
        if char not in validCharacters: return False
    
    return True

def getTokenForUserUUID(UserUUID) -> str:
    for token in tokens.values():
        if token["UUID"] == UserUUID: return token
    
    return None

def stripAccountSensitiveInfo(accountData):
    accDataCopy = copy.deepcopy(accountData)
    del accDataCopy["Password"]
    del accDataCopy["Email"]
    return accDataCopy

def getAccountFromToken(token):
    if token not in tokens.keys(): return {}
    UUID = tokens[token]["UUID"]
    accountData = accounts[UUID]
    return stripAccountSensitiveInfo(accountData)

def createAccount(username: str, password: str, email: str=""):
    global accounts
    
    # check if password is "valid"
    # idc what the password is, as long as it is 8 character long or longer
    # until it becomes a problem w/ emojis or something i'll let it be
    if len(password) < 8: return "Password too short! Must be greater than 8 characters!"
    if isUsernameValid(username) == False: return "Something is wrong with your username!"
    if isUsernameTaken(username): return "Username already in use!"
    
    # add account here
    UUID = generateUUID()
    hashedPassword = sha256HashString(sha256HashString(password))
    epochNow = getEpoch()
    
    accountData = createAccountSkeleton(
        username=username,
        password=hashedPassword,
        uuid=UUID,
        email=email,
        isBanned=False,
        isAdmin=True,
        creationEpoch=epochNow,
        pfp=f"https://api.dicebear.com/9.x/identicon/png?seed={username}",
        
        money=0, # TODO: Maybe give them some money to start with
        gameData={},
        OwnedItems=[],
        TotalXP=0,
        AllSeasonsXP={}
    )
    
    accounts[UUID] = accountData
    addTransaction(UUID, "Money", accountData["EconomyData"]["Money"], "Signup", "", epochNow)
    saveFilesIntoMemory(doAccounts=True)
    return "Success"

def loginAndGetToken(username, password):
    global accounts, tokens
    hashedPassword = sha256HashString(sha256HashString(password))
    userUUID = None
    for account in accounts.values():
        print(account, username, hashedPassword)
        if account["Username"] != username: continue
        if account["Password"] != hashedPassword: continue
        userUUID = account["UUID"]
        break
    
    if userUUID == None:
        # Couldn't find account, or credentials are wrong!
        return "Failed!"
    
    existingTokenData = getTokenForUserUUID(userUUID)
    if existingTokenData != None:
        # We are already signed in. We are going to return this.
        # If we want to invalidate tokens we can do so via logging out
        return existingTokenData
    
    # make token and return it
    tokenData = {
        "UUID": userUUID,
        "Token": generateUUID(),
    }
    tokens[ tokenData["Token"] ] = tokenData
    saveFilesIntoMemory(doTokens=True)
    return tokenData

def invalidateToken(token):
    if token not in tokens.keys(): return False
    del tokens[token]
    saveFilesIntoMemory(doTokens=True)

def deleteAccount(token):
    if token not in tokens.keys(): return False
    UUID = tokens[token]["UUID"]
    del accounts[UUID]
    del tokens[token]
    
    saveFilesIntoMemory(doAccounts=True, doTokens=True)

def updateAccountGameData(UUID, gameName, newData):
    # Try to turn the data into a JSON object if it is possible / if the game want us to
    try: newData = json.loads(newData)
    except: pass
    
    # The responsibility of the game is to fetch the game data from the user, and they will send the full complete data back
    for account in accounts.values():
        if account["UUID"] != UUID: continue
        if newData == "": del account["EconomyData"]["GameData"][gameName]
        else: account["EconomyData"]["GameData"][gameName] = newData
        
        saveFilesIntoMemory(doAccounts=True)
        return True
    return False

def awardMoney(token, amount, source, description, currency: str=None):
    if token not in tokens.keys(): return False
    if currency == None: currency = "Money"
    
    UUID = tokens[token]["UUID"]
    accounts[UUID]["EconomyData"][currency] += amount
    addTransaction(UUID, currency, amount, source, description, getEpoch())
    saveFilesIntoMemory(doAccounts=True)
    return True

def awardXP(token, amount, source, description):
    if token not in tokens.keys(): return False
    
    seasonId = getCurrentSeason()["SeasonNumber"]
    UUID = tokens[token]["UUID"]
    accounts[UUID]["EconomyData"]["TotalXP"] += amount
    accounts[UUID]["EconomyData"]["AllSeasonsXP"][seasonId] += amount
    addTransaction(UUID, "XP", amount, source, description, getEpoch())
    saveFilesIntoMemory(doAccounts=True)
    return True

def addTransaction(uuid, currency, amount, source, description, epoch):
    # Maybe we ask the client to do some calculations like asking them for a salt that will start with a few zeros in order for the transaction to go through? 
    currencySign = currency
    if currency == "Money": currencySign = "$"
    if currency == "XP": currencySign = " XP"
    
    isPlus = "+" if amount > 0 else ""
    accounts[uuid]["EconomyData"]["TransactionHistory"].append(
        f"{isPlus}{amount}{currencySign} From: {source}; Desc: {description}; Time: {epoch}"
    )
    return True

def getShopItems():
    with open("./api_data/shopItems") as f:
        return f.read()

def buyShopItem(token, itemId):
    if token not in tokens.keys(): return False # Not signed in or invalid token
    
    items = getShopItems()
    if itemId not in items.keys(): return False # Not a real item
    itemData = items[itemId]
    """ (Key to items is the itemId)
    {
        "Id": str
        "Name": str
        "Price": int
        "Currency": str (default is "Money" and this is here if I ever add future currencies, probably not though)
    }
    """
    currency = itemData["Currency"]
    price = itemData["Price"]
    
    accountData = getAccountFromToken(token)
    if itemId in accountData["EconomyData"]["OwnedItems"]: return False # Already owned
    if price > accountData["EconomyData"][currency]: return False # Too expensive
    
    # Everything is good if we make it here, process the purchase and log it
    accountData["EconomyData"]["OwnedItems"].append(itemId)
    awardMoney(token, (price * -1), "Buying from the Shop", f"User buying {itemData['Name']} (ID: {itemId})", currency=currency)
    saveFilesIntoMemory(doAccounts=True) # AwardMoney saves for us, but lets save anyways, just in case
    return True
    

def getCurrentSeason():
    with open("./api_data/seasons/currentSeason.json") as f:
        return json.load(f)

def getCurrentSeasonBattlepass():
    seasonId = getCurrentSeason()["SeasonNumber"]
    battlepassFileName = f"battlepassSeason{seasonId}.json"
    
    with open(f"./api_data/seasons/{battlepassFileName}") as f:
        return json.load(f)

def loadFilesFromRepo():
    accountsData = GH2DataRepo.readFile("accounts.json")
    if accountsData != None:
        accountsData = json.loads(accountsData)
        saveFilesIntoMemory(doAccounts=True)
    
    tokensData = GH2DataRepo.readFile("tokens.json")
    if tokensData != None:
        tokensData = json.loads(tokensData)
        saveFilesIntoMemory(doTokens=True)

def loadFilesIntoMemory():
    global accounts, tokens
    with open("./api_data/accounts.json", "r") as accountsFile:
        accounts = json.load(accountsFile)
        GH2DataRepo.updateFile(accountsFile.read(), "accounts.json", f"Updating accounts.json {getEpoch()}")
    
    with open("./api_data/tokens.json", "r") as tokensFile:
        tokens = json.load(tokensFile)
        GH2DataRepo.updateFile(tokensFile.read(), "tokens.json", f"Updating tokens.json {getEpoch()}")

def saveFilesIntoMemory(doAccounts=False, doTokens=False):
    global accounts, tokens
    
    if doAccounts:
        with open("./api_data/accounts.json", "w") as accountsFile: json.dump(accounts, accountsFile, indent=4)
    
    if doTokens:
        with open("./api_data/tokens.json", "w") as tokensFile: json.dump(tokens, tokensFile, indent=4)

def getEpoch():
    return math.floor(time.time())

def generateUUID() -> str:
    return str(uuid.uuid4())

def sha256HashString(string: str) -> str:
    encodedString = string.encode()
    return hashlib.sha256(encodedString).hexdigest()

def getAdminTOTPCode():
    return adminTOTP.now()
