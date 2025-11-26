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
        "params": [{"address": addr, "topics": ["0x5b565efe82411da98814f356d0e7bcb8f0219b8d970307c5afb4a6903a8b2e35"], "fromBlock": hex(from_block), "toBlock": "finalized" }],
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

def is_game_blacklisted(url, portal_address, game_address):
    # Create function signature for disputeGameBlacklist(IDisputeGame)
    function_signature = "0x45884d32"  # First 4 bytes of keccak256("disputeGameBlacklist(address)")
    
    # Pad the game address to 32 bytes
    padded_address = game_address.replace("0x", "").rjust(64, "0")
    
    # Construct the data payload
    data = function_signature + padded_address
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{
            "to": portal_address,
            "data": data
        }, "latest"],
        "id": 1
    }
    
    response = requests.post(url, json=payload)
    result = response.json().get("result", "0x")

    # If result is 0x00, the game is not blacklisted
    # If result is 0x01, the game is blacklisted
    if result == "0x":
        logger.warning(f"Unexpected result from disputeGameBlacklist: {result}")
        return False
    else:
        return result.strip() == "0x01" or result.strip() == "0x0000000000000000000000000000000000000000000000000000000000000001"


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
    parser.add_argument("--optimism_portal2", type=str, help="optimism portal2 contract address")
    parser.add_argument(
        "--check_interval", type=int, default=15 * 60, help="interval to query"
    )
    parser.add_argument(
        "--force_interval", type=int, default=3600 * 24, help="interval to forcibly send update"
    )
    parser.add_argument(
        "--blocks", type=int, default=7*7200, help="starting block (now - interval)"
    )
    parser.add_argument("--from_addr", type=str, default="", help="email from address")
    parser.add_argument("--to_addr", type=str, default="", help="email to address")
    parser.add_argument("--username", type=str, default="", help="email username")
    parser.add_argument("--password", type=str, default="", help="email password")
    parser.add_argument("--test_email", action="store_true", help="send a test email when start")
    args = parser.parse_args()

    # prev_balance = None
    prev_send = time.monotonic()

    if args.test_email:
        title = "test email for fdg watcher {}".format(args.fdg_factory)
        send_email(title, "", args.from_addr, args.to_addr, args.username, args.password)

    while True:
        try:
            logger.info("Checking")
            errors = 0
            blacklisted_count = 0  # Counter for blacklisted games
            skipped_count = 0  # Counter for skipped games due to missing data
            skipped_games = []  # List to store skipped game transaction hashes
            msg = ""

            bn = get_blocknumber(args.l1_rpc)
            games = get_fdg_games(args.l1_rpc, args.fdg_factory, bn - args.blocks)

            for g in games:
                info = get_fdg_game_info(args.l1_rpc, g["transactionHash"])
                # Skip if blockNumber is 0 or output is missing
                if info["blockNumber"] == 0 or not info["output"]:
                    logger.warning(f"Skipping game check due to missing data: {g['transactionHash']}")                                    
                    skipped_count += 1
                    skipped_games.append(g["transactionHash"])
                    continue
                
                l2output = get_l2output(args.l2_rpc, info["blockNumber"])
                if l2output != "0x" + info["output"]:
                    # If the output roots don't match, check if the game is blacklisted
                    # Game address is in the second topic, where the last 40 characters represent the address
                    game_topics = g["topics"]
                    # Initialize game_address with a default value in case we can't extract it
                    game_address = "0x0"
                    
                    if len(game_topics) >= 2:
                        # Extract the address part (last 40 characters) from the second topic
                        topic_data = game_topics[1]
                        game_address = "0x" + topic_data[-40:]  # Last 40 characters with 0x prefix
                    else:
                        logger.warning(f"Could not extract game address from topics: {game_topics}")
                    
                    blacklisted = False
                    
                    # Only check blacklist if we have a valid game address (not the default)
                    if args.optimism_portal2 and game_address != "0x0":
                        blacklisted = is_game_blacklisted(args.l1_rpc, args.optimism_portal2, game_address)
                        if blacklisted:
                            logger.info(f"Game {game_address} has output mismatch but is blacklisted, skipping alert")
                            blacklisted_count += 1  # Increment blacklisted counter
                        else:
                            logger.info(f"Malicious Game {game_address} is not blacklisted")
                
                    if not blacklisted:
                        msg += "error: tx {}, address {}, expected {}, actual {}\n\n".format(
                            g["transactionHash"], game_address, l2output, info["output"])
                        errors += 1

            # Add information about skipped games to the message
            if skipped_count > 0:
                msg += "Skipped games due to missing data:\n"
                for tx_hash in skipped_games:
                    msg += f"- {tx_hash}\n"
                msg += "\n"
                
            msg += "total {}, successes {}, errors {}, blacklisted {}, skipped {}".format(
                len(games), len(games)-errors-blacklisted_count-skipped_count, errors, blacklisted_count, skipped_count)

            logger.info(msg)

            if errors != 0 or time.monotonic()-prev_send > args.force_interval:
                title = "FDG {}, total {}, successes {}, errors {}, blacklisted {}, skipped {}".format(
                    args.fdg_factory, len(games), len(games)-errors-blacklisted_count-skipped_count, errors, blacklisted_count, skipped_count)
                send_email(title, msg, args.from_addr, args.to_addr, args.username, args.password)
                prev_send = time.monotonic()

            logger.info(f"Checking complete. Waiting {args.check_interval} seconds before next check.")
        except KeyboardInterrupt:
            logger.info("Exiting due to keyboard interrupt (Ctrl+C)")
            break  # Exit the while loop on Ctrl+C
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            logger.info("Continuing to next iteration...")
        
        # Sleep is outside the try-except block so it always happens, even after errors
        time.sleep(args.check_interval)

if __name__ == "__main__":
    main()