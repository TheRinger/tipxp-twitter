# import twitter
import requests
from requests_oauthlib import OAuth1
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import settings
import json


class XP_RPC():

    def __init__(self):
        self.connection = AuthServiceProxy(
            settings.RPC_URL % (settings.rpc_user, settings.rpc_password))

    def get_address(self, name):
        # commands = [["getaddressesbyaccount", name]]
        address = self.connection.getaddressesbyaccount(name)
        if address:
            address = address[0]
        else:
            address = self.connection.getaccountaddress(name)
        return address

    def show_balance(self, name):
        address = self.connection.getaddressesbyaccount(name)
        if address:
            balance = self.connection.getbalance(name)
        else:
            address = self.connection.getaccountaddress(name)
            balance = self.connection.getbalance(name)
        print(balance)
        return balance

    def move_balance(self, name, to_name, amount):
        address = self.connection.getaddressesbyaccount(name)
        to_address = self.connection.getaddressesbyaccount(to_name)
        if address and to_address:
            # req = self.connection.move(name, to_name, amount)
            req = self.connection.move(name, to_name, amount)
        elif address:
            self.connection.getaccountaddress(to_name)
            req = self.connection.move(name, to_name, amount)
        else:
            req = "Error"
        return req

    def send_from(slef, name, address, amount):
        pass


class Twitter():

    def __init__(self):
        self.xpd = XP_RPC()
        self.auth_stream = OAuth1(settings.CONSUMER_KEY_STREAM, settings.CONSUMER_SECRET_STREAM,
                           settings.ACCESS_TOKEN_STREAM, settings.ACCESS_TOKEN_SECRET_STREAM)
        self.auth_reply = OAuth1(settings.CONSUMER_KEY_REPLY, settings.CONSUMER_SECRET_REPLY,
                           settings.ACCESS_TOKEN_REPLY, settings.ACCESS_TOKEN_SECRET_REPLY)

    def reply(self, text, reply_token):
        params = {
            "status": text,
            "in_reply_to_status_id": reply_token,
            "auto_populate_reply_metadata": "true"
        }
        req = requests.post(
            "https://api.twitter.com/1.1/statuses/update.json", auth=self.auth_reply, data=params)
        return req

    def detect(self, tweet):
        print("Detecting...")
        m = tweet["text"].split(" ")
        if m[0] == "@tip_XPchan":
            command = m[1]
            lang = tweet["user"]["lang"]
            address_name = "tipxpchan-" + tweet["user"]["id_str"]

            if command == "tip":
                print("tip in")
                amount = m[3]
                if m[2][0] == "@":
                    to_name = "tipxpchan-" + self.get_id(m[2][1:])
                    balance = self.xpd.show_balance(address_name)
                    amount = float(amount)
                    if balance >= amount:
                        if self.xpd.move_balance(address_name, to_name, amount):
                            if lang == "ja":
                                text = "XPちゃんより%sさんにお届けものだよっ！ %fXP\n『@￰tip_XPchan balance』で残高確認が行えるよ！" % (m[2], amount)
                            else:
                                text = "Present for %s! Sent %fXP!"
                            req = self.reply(text, tweet["id"])
                    else:
                        if lang == "ja":
                            text = "残高が足りないよ〜 所持XP:%f" % balance
                        else:
                            text = "Not enough balance! XP:%f" % balance
                        req = self.reply(text, tweet["id"])
                else:
                    print("エラーだよっ！よく確認してね！")

            elif command == "donate":
                print("donate in")
                amount = m[2]
                to_name = "tipxpchan-940589020509192193"
                balance = self.xpd.show_balance(address_name)
                amount = float(amount)
                if balance >= amount:
                    if self.xpd.move_balance(address_name, to_name, amount):
                        if lang == "ja":
                            text = "@%s 開発へのご支援ありがとうございます！" % tweet["user"]["name"]
                        else:
                            text = "@%s Thank you for donation！" % tweet["user"]["name"]
                        req = self.reply(text, tweet["id"])
                else:
                    if lang == "ja":
                        text = "残高が足りないよ〜 所持XP:%f" % balance
                    else:
                        text = "Not enough balance! XP:%f" % balance
                    req = self.reply(text, tweet["id"])

            elif command == "deposit":
                print("deposit in")
                if lang == "ja":
                    text = "%sさんのアドレスは「%s」だよっ！" % (
                        tweet["user"]["name"], self.xpd.get_address(address_name))
                else:
                    text = "%s 's address is 「%s」！" % (
                        tweet["user"]["name"], self.xpd.get_address(address_name))
                req = self.reply(text, tweet["id"])

            elif command == "withdraw":
                print("withdraw in")
                pass

            elif command == "withdrawall":
                print("withdrawall in")
                pass

            elif command == "balance":
                print("balance in")
                if lang == "ja":
                    text = "%sさんの保有XPは%fXPだよん！" % (
                        tweet["user"]["name"], self.xpd.show_balance(address_name))
                else:
                    text = "%s 's balance is %fXP！" % (
                        tweet["user"]["name"], self.xpd.show_balance(address_name))
                req = self.reply(text, tweet["id"])

            else:
                print("command error")
                # text = "エラーだよっ！よく確認してね！"
                # req = self.reply(text, tweet["id"])

        else:
            pass

    def get_id(self, name):
        params = {
            "screen_name": name,
        }
        user_id = requests.get("https://api.twitter.com/1.1/users/show.json", auth=self.auth_reply, params=params).json()["id_str"]
        return user_id


def main():
    url = "https://stream.twitter.com/1.1/statuses/filter.json"
    twitter = Twitter()
    # print(twitter.detect(tweet))
    _stream = requests.post(url, auth=twitter.auth_stream, stream=True, data={"track":"@tip_XPchan"})
    for _line in _stream.iter_lines():
        try:
            _doc = json.loads(_line.decode("utf-8"))
            print(_doc)
            print(twitter.detect(_doc))
        except:
            print("エラー")
            pass


if __name__ == '__main__':
    main()
