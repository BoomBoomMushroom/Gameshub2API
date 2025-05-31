import os
#os.system('pip install PyGithub')

import flask
from flask import request
import json
import GH2API

app = flask.Flask(__name__)

def responseMake(r):
    resp = flask.Response(json.dumps(r))
    resp.headers['Access-Control-Allow-Origin'] = "*"
    return resp

@app.route("/")
def home():
    return responseMake("Hello "+request.method+" user!")

@app.route("/isUsernameUsable")
def isUsernameUsable():
    try:
        username_query = str(request.args.get('username'))
    except:
        flask.abort(400)
    
    if GH2API.isUsernameValid(username_query) == False: return responseMake("Username is not allowed!")
    if GH2API.isUsernameTaken(username_query): return responseMake("Username Taken!")
    return responseMake(True)

@app.route("/accountFromToken")
def accountFromToken():
    try:
        token_query = str(request.args.get('token'))
    except:
        flask.abort(400)
    
    accountData = GH2API.getAccountFromToken(token_query)
    return responseMake(accountData)

@app.route("/createAccount")
def createAccount():
    try:
        username_query = str(request.args.get('username'))
        password_query = str(request.args.get('password'))
    except:
        flask.abort(400)
    
    # I don't have a way to verify email legitimacy so I will just make it accept whatever
    #   and when I can verify emails i'll either reset all emails or tell them to verify them.
    try:
        email_query = str(request.args.get('email'))
    except: email_query = ""
    
    responseData = GH2API.createAccount(username_query, password_query, email_query)
    return responseMake(responseData)

@app.route("/login")
def login():
    try:
        username_query = str(request.args.get('username'))
        password_query = str(request.args.get('password'))
    except:
        flask.abort(400)
    
    tokenData = GH2API.loginAndGetToken(username_query, password_query)
    return responseMake(tokenData)

@app.route("/updateAccountGameData")
def updateAccountGameData():
    try:
        token_query = str(request.args.get('token'))
        game_name_query = str(request.args.get('gameName'))
        game_data_query = str(request.args.get('gameData'))
    except:
        flask.abort(400)
    
    accountData = GH2API.getAccountFromToken(token_query)
    isSuccess = GH2API.updateAccountGameData(accountData["UUID"], game_name_query, game_data_query)
    return responseMake(isSuccess)

@app.route("/deleteAccount")
def deleteAccount():
    try:
        token_query = str(request.args.get('token'))
    except:
        flask.abort(400)
    
    isSuccess = GH2API.deleteAccount(token_query)
    return responseMake(isSuccess)

@app.route("/invalidateToken")
def invalidateToken():
    try:
        token_query = str(request.args.get('token'))
    except:
        flask.abort(400)
    
    isSuccess = invalidateToken(token_query)
    return responseMake(isSuccess)

@app.route("/awardMoney")
def awardMoney():
    try:
        token_query = str(request.args.get('token'))
        amount_query = int(request.args.get('amount'))
        source_query = str(request.args.get('source'))
        description_query = str(request.args.get('description'))
    except:
        flask.abort(400)
    
    isSuccess = GH2API.awardMoney(token_query, amount_query, source_query, description_query)
    return responseMake(isSuccess)

@app.route("/getShopItems")
def getShopItems():
    return responseMake( getShopItems() )

@app.route("/buyShopItem")
def buyShopItem():
    try:
        token_query = str(request.args.get('token'))
        itemId_query = int(request.args.get('itemId'))
    except:
        flask.abort(400)

    isSuccess = GH2API.buyShopItem(token_query, itemId_query)
    return responseMake(isSuccess)
    
@app.route("/getCurrentSeason")
def getCurrentSeason():
    return responseMake( GH2API.getCurrentSeason() )

@app.route("/getCurrentSeasonBattlepass")
def getCurrentSeasonBattlepass():
    return responseMake( GH2API.getCurrentSeasonBattlepass() )

@app.route("/awardXP")
def awardXP():
    try:
        token_query = str(request.args.get('token'))
        amount_query = int(request.args.get('amount'))
        source_query = str(request.args.get('source'))
        description_query = str(request.args.get('description'))
    except:
        flask.abort(400)
    
    isSuccess = GH2API.awardXP(token_query, amount_query, source_query, description_query)
    return responseMake(isSuccess)

@app.route("/restart")
def restart():
    try:
        totp_code_query = str(request.args.get('code'))
    except:
        flask.abort(400)
    
    if totp_code_query != GH2API.getAdminTOTPCode(): return responseMake("Wrong Code!")
    exit()

@app.route("/pullAccountsAndTokensFromRepo")
def pullAccountsAndTokensFromRepo():
    try:
        totp_code_query = str(request.args.get('code'))
    except:
        flask.abort(400)
    
    if totp_code_query != GH2API.getAdminTOTPCode(): return responseMake("Wrong Code!")
    
    GH2API.loadFilesFromRepo()
    return responseMake(True)

GH2API.loadFilesIntoMemory()
app.run(host="0.0.0.0",port=7770)