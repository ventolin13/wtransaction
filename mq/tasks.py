from __future__ import absolute_import, unicode_literals
import config

from celery.decorators import periodic_task
from celery.task.schedules import crontab
from decimal import Decimal
from mongoengine import Q

from mq.celery import app as capp
from models.models import connect_db, Transaction, Tx, Block, Work

import time
import datetime
import bitcoinrpc
import traceback
'''
>>> t
CTransaction((CTxIn(COutPoint(lx('87a157f3fd88ac7907c05fc55e271dc4acdc5605d187d646604ca8c0e9382e03'), 0),
CScript([x('3046022100c352d3dd993a981beba4a63ad15c209275ca9470abfcd57da93b58e4eb5dce82022100840792bc1f456062819f15d33ee7055cf7b5ee1af1ebcc6028d9cdb1c3af774801'),
x('04f46db5e9d61a9dc27b8d64ad23e7383a4e6ca164593c2527c038c0857eb67ee8e825dca65046b82c9331586c82e0fd1f633f25f87c161bc6f8a630121df2b3d3')]), 0xffffffff),),
(CTxOut(5.56*COIN, CScript([OP_DUP, OP_HASH160, x('c398efa9c392ba6013c5e04ee729755ef7f58b32'), OP_EQUALVERIFY, OP_CHECKSIG])),
CTxOut(44.44*COIN, CScript([OP_DUP, OP_HASH160, x('948c765a6914d43f2a7ac177da2c2f6b52de3d7c'), OP_EQUALVERIFY, OP_CHECKSIG]))), 0, 1)

>>> r
bitcoinrpc.data.TransactionInfo(hash=u'fff2525b8931402dd09222c50775608f75787bd2b87e56995a7bdd30f79702c4',
vout=[{u'scriptPubKey': {u'reqSigs': 1, u'hex': u'76a914c398efa9c392ba6013c5e04ee729755ef7f58b3288ac',
u'addresses': [u'1JqDybm2nWTENrHvMyafbSXXtTk5Uv5QAn'],
u'asm': u'OP_DUP OP_HASH160 c398efa9c392ba6013c5e04ee729755ef7f58b32 OP_EQUALVERIFY OP_CHECKSIG', u'type': u'pubkeyhash'},
u'value': Decimal('5.56000000'), u'n': 0}, {u'scriptPubKey': {u'reqSigs': 1, u'hex': u'76a914948c765a6914d43f2a7ac177da2c2f6b52de3d7c88ac',
u'addresses': [u'1EYTGtG4LnFfiMvjJdsU7GMGCQvsRSjYhx'], u'asm': u'OP_DUP OP_HASH160 948c765a6914d43f2a7ac177da2c2f6b52de3d7c OP_EQUALVERIFY OP_CHECKSIG',
u'type': u'pubkeyhash'}, u'value': Decimal('44.44000000'), u'n': 1}],
blockhash=u'000000000003ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506',
vin=[{u'sequence': 4294967295, u'scriptSig':
{u'hex': u'493046022100c352d3dd993a981beba4a63ad15c209275ca9470abfcd57da93b58e4eb5dce82022100840792bc1f456062819f15d33ee7055cf7b5ee1af1ebcc6028d9cdb1c3af7748014104f46db5e9d61a9dc27b8d64ad23e7383a4e6ca164593c2527c038c0857eb67ee8e825dca65046b82c9331586c82e0fd1f633f25f87c161bc6f8a630121df2b3d3',
u'asm': u'3046022100c352d3dd993a981beba4a63ad15c209275ca9470abfcd57da93b58e4eb5dce82022100840792bc1f456062819f15d33ee7055cf7b5ee1af1ebcc6028d9cdb1c3af7748[ALL]
04f46db5e9d61a9dc27b8d64ad23e7383a4e6ca164593c2527c038c0857eb67ee8e825dca65046b82c9331586c82e0fd1f633f25f87c161bc6f8a630121df2b3d3'},
u'vout': 0, u'txid': u'87a157f3fd88ac7907c05fc55e271dc4acdc5605d187d646604ca8c0e9382e03'}],
hex=u'0100000001032e38e9c0a84c6046d687d10556dcacc41d275ec55fc00779ac88fdf357a187000000008c493046022100c352d3dd993a981beba4a63ad15c209275ca9470abfcd57da93b58e4eb5dce82022100840792bc1f456062819f15d33ee7055cf7b5ee1af1ebcc6028d9cdb1c3af7748014104f46db5e9d61a9dc27b8d64ad23e7383a4e6ca164593c2527c038c0857eb67ee8e825dca65046b82c9331586c82e0fd1f633f25f87c161bc6f8a630121df2b3d3ffffffff0200e32321000000001976a914c398efa9c392ba6013c5e04ee729755ef7f58b3288ac000fe208010000001976a914948c765a6914d43f2a7ac177da2c2f6b52de3d7c88ac00000000', txid=u'fff2525b8931402dd09222c50775608f75787bd2b87e56995a7bdd30f79702c4',
blocktime=1293623863, version=1, confirmations=352006, time=1293623863, locktime=0, vsize=259, size=259)
'''
@capp.task(ignore_result=True)
def ctest(name):
    print "ctest %s" % name





@periodic_task(run_every=datetime.timedelta(seconds=10*60))
def worker_read_lost_block():
    connect_db()
    work = Work.objects().first()
    if not work or work.main != "on":
        print work.main
        return

    conn = bitcoinrpc.connect_to_remote(config.rpc_user, config.rpc_password, host='localhost', port=8332)
    bs = Block.objects(status="new")
    if bs.count() > 32:
        read_next_block(conn=conn, b=bs[0], work=work, is_mg_connectd=True)
        read_next_block(conn=conn, b=bs[1], work=work, is_mg_connectd=True)
    elif bs.count() > 16:
        read_next_block(conn=conn, b=bs[0], work=work, is_mg_connectd=True)
    else:
        return



@periodic_task(run_every=datetime.timedelta(seconds=60))
def worker_read_next_block1():
    connect_db()
    work = Work.objects().first()
    if not work or work.main != "on":
        print work.main
        return

    conn = bitcoinrpc.connect_to_remote(config.rpc_user, config.rpc_password, host='localhost', port=8332)
    for i in range(work.num):
        read_next_block(conn=conn, b=None, work=work, is_mg_connectd=True)


def read_next_block(conn=None, b=None, work=None, is_mg_connectd=False):
    if not is_mg_connectd:
        connect_db()
    if not work:
        work = Work.objects().first()

    if not conn:
        conn = bitcoinrpc.connect_to_remote(config.rpc_user, config.rpc_password, host='localhost', port=8332)
    
    num = 0
    if not b:
        b = Block.objects().order_by("-num").first()
        # if b and b.status == "new" and work.block_try < 7:
        #     time_sleep = 2**work.block_try
        #     work.block_try += 1
        #     work.save()
        #     print "last creatting... %s seconds delay" % time_sleep
        #     time.sleep(time_sleep)
        #     return
        # elif b and b.status == "new" and work.block_try == 7:
        #     work.block_try = 0
        #     work.save()
        #     Tx.objects(block_hash=b.hash).delete()
        #     Transaction.objects(block_hash=b.hash).delete()
        #     Block.objects(hash=b.hash).delete()
        #     return
        # elif Block.objects(status="new"):
        #     print "creatting..."
        #     return
        
        if b : num = b.num
        num += 1
    
    
        block_hash = conn.getblockhash(num)
        block = conn.getblock(block_hash)
        if block["confirmations"] < 10:
            print "block confirmations is not enough: %s" % block["confirmations"]
            return
        if b and b.hash != block["previousblockhash"]:
            print b.hash, "not equal previousblockhash", block["previousblockhash"]
            return

        if b and b.nhash != block["hash"]:
            print b.nhash, "not equal current", block["hash"]
            return

        b = Block(num=num,
                hash=block["hash"],
                phash=block["previousblockhash"],
                nhash=block["nextblockhash"],
                mroot=block["merkleroot"],
                vtx=block["tx"],
                created=datetime.datetime.fromtimestamp(block["time"]),
                status="new")
        try:
            b.save(write_concern={"w": config.wnum, "fsync": True})
        except Exception:
            print "try concurrency block save - failed!"
            return


    Tx.objects(block_hash=b.hash).delete()
    Transaction.objects(block_hash=b.hash).delete()

    for tx_hash in b.vtx:
        tx = conn.getrawtransaction(tx_hash)
        is_duplicate = bool(Tx.objects(hash=tx_hash).update_one(is_duplicate=True))
        x = Tx(block_hash=b.hash,
                hash=tx_hash,
                is_duplicate=is_duplicate, 
                status="",
                created=datetime.datetime.fromtimestamp(tx.time))

        '''
        TODO update x:
        fee =                       DecimalField(default=0)
        ins                         ListField()
        outs =                      ListField()
        '''
        vouts = []
        amount_out = Decimal(0)
        for i, vout in enumerate(tx.vout):
            if "addresses" not in vout["scriptPubKey"]:
                print tx_hash, i, " not found addresses"
                address = ""
                x.status += "not_found"
            elif len(vout["scriptPubKey"]["addresses"]) > 1:
                print tx_hash, i, " - toooooo much addresses"
                address = ""
                x.status += "many_address"
            else:
                address = vout["scriptPubKey"]["addresses"][0]
            
            type = vout["scriptPubKey"]["type"]
            amount = Decimal(vout["value"])
            amount_out += amount
            t = Transaction(block_hash=b.hash,
                    hash=tx_hash,
                    address = address,
                    amount=amount,
                    vout=i,
                    type=type,
                    ins=[],
                    is_spent=False,
                    created=datetime.datetime.fromtimestamp(tx.time),
                    outs=[],
                    fee=0,
                    dfee=0)
            vouts.append(t)

        out_addresses = [t.address for t in vouts]

        in_addresses = []
        amount_in = Decimal(0)
        vins = []
        is_coinbase = False
        if len(tx.vin) == 1 and tx.vin[0].get("coinbase"):
            x.ins = []
            is_coinbase = True
        else:
            for vin in tx.vin:
                n = vin["vout"]
                spent_t = Transaction.objects(Q(vout=n)&Q(hash=vin["txid"])).first()
                if not spent_t or spent_t.block_hash == b.hash or Block.objects(Q(hash=spent_t.block_hash)&Q(status="new")).count():
                    tx_vin = conn.getrawtransaction(vin["txid"])
                    if "addresses" not in tx_vin.vout[n]["scriptPubKey"]:
                        address = ""
                        x.status += "not_found_in"
                    else:
                        address = tx_vin.vout[n]["scriptPubKey"]["addresses"][0]
                    
                    in_hash = vin["txid"]
                    in_created = datetime.datetime.fromtimestamp(tx_vin.time)
                    amount = Decimal(tx_vin.vout[n]["value"])
                else:
                    address = spent_t.address
                    in_hash = spent_t.hash
                    in_created = spent_t.created
                    amount = Decimal(spent_t.amount)

                amount_in += amount
                in_addresses.append(address)
                t = Transaction(block_hash=b.hash,
                        hash=tx_hash,
                        address=address,
                        amount=-amount,
                        in_hash=in_hash,
                        in_created=in_created,
                        vout=-1,
                        outs=out_addresses,
                        created=datetime.datetime.fromtimestamp(tx.time),
                        )
                vins.append(t)

        for t in vouts:
            t.ins = in_addresses
            t.save() #write_concirn
            x.outs.append(t.id)

        x.fee = Decimal(0) if is_coinbase else (amount_in - amount_out)
        for t in vins:
            t.fee = x.fee
            if amount_in:
                t.dfee = -x.fee*t.amount/amount_in
            else:
                t.dfee = Decimal(0)
                x.status += "zero_in"
            t.save() #write_concirn
            x.ins.append(t.id)

        print "%s, %s: in %s, out %s" % (b.num, t.hash, amount_in, amount_out)
        x.save()

    Block.objects(id=b.id).update_one(status="done", write_concern={"w": config.wnum, "fsync": True})







'''
    block_hash =                StringField()
    hash =                      StringField()
    address =                   StringField(required=True)
    amount =                    DecimalField(default=0)

    #amount > 0
    vout =                      IntField()
    ins =                       ListField(default=[])
    is_spent =                  BooleanField(default=False)

    #amount < 0
    outs =                      ListField(default=[])
    fee =                       DecimalField(default=0)
    dfee =                      DecimalField(default=0)

    created =                   DateTimeField()

'''

















































