# Prerequisite

Run `pip install aiortc`

# How to Run

## Python (Offer) => Web (Answer)

1. Run `python3 datachannel-cli/cli.py offer` and copy the offer SDP JSON message.

2. Open `webrtc.html` in a browser, paste the JSON message, and click submit.

3. Copy the answer SDP JSON message from the browser and paste it in the python3.

4. The `webrtc.html` in the browser should receive the data from python3 in console.

## Web (Offer) => Python (Answer)

1. Open `webrtc.html#1` in a browser and copy the offer SDP JSON message.

2. Run `python3 datachannel-cli/cli.py answer` and paste the JSON message.

3. Copy the answer SDP JSON message in python3, paste it in the browser, and click submit.

4. The `webrtc.html` in the browser should print `CONNECTED` in console.


