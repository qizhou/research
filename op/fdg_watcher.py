import requests
import time
import logging
import argparse
import smtplib
from email.message import EmailMessage


FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)
logging.getLogger("jsonrpcclient.client.request").setLevel(logging.WARNING)
logging.getLogger("jsonrpcclient.client.response").setLevel(logging.WARNING)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# def query(rpc, *args):
#     jsonrpcclient.requst
#     retry, resp = 0, None
#     while retry <= 5:
#         try:
#             resp = jsonrpcclient.request(, endpoint, *args)
#             break
#         except Exception:
#             retry += 1
#             time.sleep(0.5)
#     return resp

def get_blocknumber(url):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1,
    }

    response = requests.post(url, json=payload)

    result = response.json()
    return int(result['result'], 16)

def get_fdg_games(url, addr, from_block):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getLogs",
        "params": [{"address": addr, "topic": "0x5b565efe82411da98814f356d0e7bcb8f0219b8d970307c5afb4a6903a8b2e35", "fromBlock": hex(from_block), "toBlock": "finalized" }],
        "id": 1,
    }

    response = requests.post(url, json=payload)

    return response.json()["result"]

def get_fdg_game_info(url, txhash):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionByHash",
        "params": [txhash],
        "id": 1,
    }

    response = requests.post(url, json=payload)
    input = response.json()["result"]["input"]

    return {"output": input[10+64:10+2*64], "blockNumber": int(input[10+4*64:10+5*64], 16)}

def get_l2output(url, blocknum):
    payload = {
        "jsonrpc": "2.0",
        "method": "optimism_outputAtBlock",
        "params": [hex(blocknum)],
        "id": 1,
    }

    response = requests.post(url, json=payload)

    result = response.json()["result"]
    return result["outputRoot"]

def send_email(title, msg, from_addr, to_addr, username, password):
    emsg = EmailMessage()
    emsg["Subject"] = title
    emsg["From"] = from_addr
    emsg["To"] = to_addr
    emsg.set_content(msg)
    logger.info(title)
    with smtplib.SMTP(host="smtp.gmail.com", port=587) as s:
        s.ehlo()
        s.starttls()
        s.login(username, password)
        s.send_message(emsg)

def main():
    global HOST, PORT
    parser = argparse.ArgumentParser()
    parser.add_argument("--fdg_factory", type=str, help="fdg factory address")
    parser.add_argument("--l1_rpc", type=str, help="l1 rpc")
    parser.add_argument("--l2_rpc", type=str, help="l2_rpc")
    parser.add_argument(
        "--check_interval", type=int, default=15 * 60, help="interval to query"
    )
    parser.add_argument(
        "--force_interval", type=int, default=None, help="interval to forcibly send update"
    )
    parser.add_argument(
        "--blocks", type=int, default=7*7200, help="starting block (now - interval)"
    )
    parser.add_argument("--from_addr", type=str, default="", help="email from address")
    parser.add_argument("--to_addr", type=str, default="", help="email to address")
    parser.add_argument("--username", type=str, default="", help="email username")
    parser.add_argument("--password", type=str, default="", help="email password")
    parser.add_argument("--test_email", type=bool, default=False, help="send a test email when start")

    args = parser.parse_args()

    # prev_balance = None
    prev_send = time.monotonic()

    if args.test_email:
        title = "test email for {}".format(args.recipient)
        send_email(title, "", args.from_addr, args.to_addr, args.username, args.password)

    bn = get_blocknumber(args.l1_rpc)
    games = get_fdg_games(args.l1_rpc, args.fdg_factory, bn - args.blocks)

    while True:
        logger.info("Checking")
        errors = 0
        msg = ""
        for g in games:
            info = get_fdg_game_info(args.l1_rpc, g["transactionHash"])
            l2output = get_l2output(args.l2_rpc, info["blockNumber"])
            if l2output != "0x" + info["output"]:
                msg += "error: game {}, expected {}, actual {}\n".format(g["transactionHash"], l2output,info["output"])
                errors += 1

        msg += "total {}, successes {}, errors {}".format(len(games), len(games)-errors, errors)

        logger.info("FDG error!")
        logger.info(msg)

        if errors != 0 or time.monotonic()-prev_send > args.force_interval:
            title = "FDG {}, total {}, successes {}, errors {}".format(args.fdg_factory, len(games), len(games)-errors, errors)
            send_email(msg, args.from_addr, args.to_addr, args.username, args.password)
            prev_send = time.monotonic()

        time.sleep(args.check_interval)

if __name__ == "__main__":
    main()