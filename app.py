from __future__ import unicode_literals

import config
import bitcoin
import bitcoin.rpc

from flask import Flask, abort, after_this_request, request, jsonify, g, url_for, Response, Blueprint, render_template
from models.models import connect_db, FWallet, RWallet
from werkzeug.contrib.fixers import ProxyFix
from bitcoin.core import COIN, b2lx

from mq.tasks import pay_now

connect_db()
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config["SECRET_KEY"] = "bincoin.org"

def response_error(reason, code):
    response = {"result":"error", "error_code":code, "reason":reason}
    return (jsonify(response), code)


@app.route("/test", methods=["GET"])
def route_test():
    return (jsonify({"result": "success"}), 200)


@app.route("/payme", methods=["POST"])
def route_payme():
    wallet = request.form["wallet"]
    proxy = bitcoin.rpc.Proxy("http://%s:%s@127.0.0.1:8332/" % (config.rpc_user, config.rpc_password))
    res = proxy.validateaddress(wallet)
    if not res["isvalid"]:
        return response_error("Bitcoin addres is not valid", 400)

    print FWallet.objects(bitcoinaddress=wallet).count()
    
    if FWallet.objects(bitcoinaddress=wallet).count():
        print "This bitcoin address already registred"
        return response_error("This bitcoin address already registred", 400)        
    
    print "fine"
    w = FWallet(bitcoinaddress=wallet)
    w.save(write_concern={"w": config.wnum, "fsync": True})
    res = pay_now(proxy, w)
    if not res:
        return response_error("Can not make payment", 400)
    return (jsonify({"result": "success"}), 200)



@app.route("/makewallet", methods=["POST"])
def route_makewallet():
    proxy = bitcoin.rpc.Proxy("http://%s:%s@127.0.0.1:8332/" % (config.rpc_user, config.rpc_password))
    wallet = str(proxy.getnewaddress("binfirst"))
    
    w = RWallet(bitcoinaddress=wallet)
    w.save(write_concern={"w": config.wnum, "fsync": True})
    
    return (jsonify({"result": "success", "wallet": wallet}), 200)


@app.route("/", methods=["GET"])
def route_main():
    proxy = bitcoin.rpc.Proxy("http://%s:%s@127.0.0.1:8332/" % (config.rpc_user, config.rpc_password))
    balance = 1.0*proxy.getbalance()/COIN
    
    fws = FWallet.objects().order_by("-created_time")[:10]
    fwallets = [(w.bitcoinaddress, "%.5f" % w.score) for w in fws]

    rws = RWallet.objects().order_by("-created_time")[:10]
    rwallets = [(w.bitcoinaddress, "%.5f" % w.score, w.status) for w in rws]

    cws = RWallet.objects(status="paid").order_by("-created_time")[:10]
    cwallets = [(w.bitcoinaddress, "%.5f" % w.score) for w in cws]

    params = {"balance": balance,
            "fwallets": fwallets,
            "rwallets": rwallets,
            "cwallets": cwallets,
            }
    return render_template("main.html", **params)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)