CIRCUITS_DIR=../../circuits
BUILD_DIR=../../build
PHASE1=$BUILD_DIR/pot18_final.ptau
CIRCUIT_NAME=$1

if [ ! -d "$BUILD_DIR" ]; then
    echo "No build directory found. Creating build directory..."
    mkdir -p "$BUILD_DIR"
fi

echo "****COMPILING CIRCUIT****"
start=`date +%s`
set -x
circom $CIRCUITS_DIR/$CIRCUIT_NAME.circom --r1cs --wasm --sym --c --wat --output "$BUILD_DIR" || exit
{ set +x; } 2>/dev/null
end=`date +%s`
echo "DONE ($((end-start))s)"


if [ -f "$PHASE1" ]; then
    echo "Found Phase 1 ptau file"
else
    echo "No Phase 1 ptau file found. Exiting..."
    exit 1
fi

echo "****GENERATING ZKEY 0****"
start=`date +%s`
npx snarkjs groth16 setup "$BUILD_DIR"/"$CIRCUIT_NAME".r1cs "$PHASE1" "$BUILD_DIR"/"$CIRCUIT_NAME"_0.zkey || exit
end=`date +%s`
echo "DONE ($((end-start))s)"

echo "****GENERATING FINAL ZKEY****"
start=`date +%s`
NODE_OPTIONS="--max-old-space-size=56000" npx snarkjs zkey beacon "$BUILD_DIR"/"$CIRCUIT_NAME"_0.zkey "$BUILD_DIR"/"$CIRCUIT_NAME".zkey 12FE2EC467BD428DD0E966A6287DE2AF8DE09C2C5C0AD902B2C666B0895ABB75 10 -n="Final Beacon phase2" || exit
end=`date +%s`
echo "DONE ($((end-start))s)"

echo "****GENERATING VERIFICATION KEY****"
start=`date +%s`
NODE_OPTIONS="--max-old-space-size=56000" npx snarkjs zkey export verificationkey  "$BUILD_DIR"/"$CIRCUIT_NAME".zkey "$BUILD_DIR"/"$CIRCUIT_NAME"_verification_key.json || exit

end=`date +%s`
echo "DONE ($((end-start))s)"