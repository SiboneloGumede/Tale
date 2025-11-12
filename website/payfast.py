import requests
import hashlib
import urllib.parse

passPhrase = 'MatutU2103tale'

def dataToString(dataArray, passPhrase = ''):
    pfParamString = ""
    for key in dataArray:
        # Get all the data from PayFast and prepare parameter string
        pfParamString += key + "=" + urllib.parse.quote_plus(dataArray[key].replace("+", " ")) + "&"
    # After looping through, cut the last & or append your passphrase
    pfParamString = pfParamString[:-1]
    if passPhrase != '':
        pfParamString += f"&passphrase={passPhrase}"
    return pfParamString

def generatePaymentIdentifier(pfParamString):
    url = "https://www.payfast.co.za/onsite/process"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }
    response = requests.post(url, data=pfParamString, headers=headers)
    try:
        responseJson = response.json()
        uuid = responseJson.get('uuid')
        return uuid
    except Exception:
        return False


def generateSignature(dataArray, passPhrase = ''):
    payload = dataToString(dataArray, passPhrase)
    return hashlib.md5(payload.encode()).hexdigest()
    

def create_payment(amount, item_name, success, cancel, notify):
    url = "https://www.payfast.co.za/eng/process?merchant_id=17547784&merchant_key=f94fol0ztgcrc&return_url={}&cancel_url={}&notify_url={}&amount={}&item_name={}".format(success,
        cancel, notify, amount, item_name)
    return url
