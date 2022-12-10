CIRCUITS_DIR=../../circuits
BUILD_DIR=../../build
INPUT_DIR=../../input
PHASE1=$BUILD_DIR/pot18_final.ptau
CIRCUIT_NAME=$1
WITNESS=$BUILD_DIR/witness_"$CIRCUIT_NAME".wtns
PROOF=$BUILD_DIR/proof_"$CIRCUIT_NAME".json
PUBLIC=$BUILD_DIR/public_"$CIRCUIT_NAME".json

if [ ! -d "$BUILD_DIR" ]; then
    echo "No build directory found. Creating build directory..."
    mkdir -p "$BUILD_DIR"
fi

echo "****GENERATING WITNESS****"
start=`date +%s`
set -x
node "$BUILD_DIR"/"$CIRCUIT_NAME"_js/generate_witness.js "$BUILD_DIR"/"$CIRCUIT_NAME"_js/$CIRCUIT_NAME.wasm $INPUT_DIR/input_$CIRCUIT_NAME.json $WITNESS
{ set +x; } 2>/dev/null
end=`date +%s`
echo "DONE ($((end-start))s)"

echo "****GENERATING PROOF****"
start=`date +%s`
set -x
snarkjs groth16 prove "$BUILD_DIR"/"$CIRCUIT_NAME".zkey $WITNESS $PROOF $PUBLIC
{ set +x; } 2>/dev/null
end=`date +%s`
echo "DONE ($((end-start))s)"

echo "****VERIFYING PROOF****"
start=`date +%s`
set -x
snarkjs groth16 verify "$BUILD_DIR"/"$CIRCUIT_NAME"_verification_key.json $PUBLIC $PROOF
{ set +x; } 2>/dev/null
end=`date +%s`
echo "DONE ($((end-start))s)"