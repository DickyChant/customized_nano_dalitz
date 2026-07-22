import numpy as np, xgboost as xgb, onnx, onnxruntime as ort
from onnxmltools.convert import convert_xgboost
from onnxmltools.convert.common.data_types import FloatTensorType

SRC = "/mnt/vdb/Codes/HDalitzEle_ref/models_json"
OUT = "/mnt/vdb/Codes/HDalitzEle_ref/models_onnx"
import os; os.makedirs(OUT, exist_ok=True)

models = {"M1EB": 20, "M1EE": 20, "M2EB": 22, "M2EE": 22}
rng = np.random.RandomState(1234)

for k, nf in models.items():
    b = xgb.Booster(); b.load_model(f"{SRC}/HDalitzMergedID_{k}.json")
    assert b.num_features() == nf, (k, b.num_features(), nf)
    onx = convert_xgboost(b, initial_types=[("input", FloatTensorType([None, nf]))],
                          target_opset=13)
    outp = f"{OUT}/HDalitzMergedID_{k}.onnx"
    with open(outp, "wb") as f:
        f.write(onx.SerializeToString())

    # --- validate ONNX vs xgboost on random + realistic feature rows ---
    sess = ort.InferenceSession(outp, providers=["CPUExecutionProvider"])
    out_names = [o.name for o in sess.get_outputs()]
    X = rng.uniform(-3, 3, size=(500, nf)).astype(np.float32)
    xgb_p = b.predict(xgb.DMatrix(X))               # (500, 3) softprob
    ort_out = sess.run(None, {"input": X})
    # pick the (N,3) float output (probabilities), handling zipmap seq-of-maps
    prob = None
    for name, val in zip(out_names, ort_out):
        arr = None
        if isinstance(val, np.ndarray) and val.ndim == 2 and val.shape[1] == 3:
            arr = val
        elif isinstance(val, list) and val and isinstance(val[0], dict):
            arr = np.array([[d[c] for c in sorted(d)] for d in val], dtype=np.float32)
        if arr is not None:
            prob = arr
    assert prob is not None, ("no prob output", out_names, [type(v) for v in ort_out])
    maxdiff = float(np.max(np.abs(prob - xgb_p)))
    meandiff = float(np.mean(np.abs(prob - xgb_p)))
    print(f"{k}: nf={nf} outputs={out_names} maxAbsDiff={maxdiff:.2e} meanAbsDiff={meandiff:.2e} "
          f"class0[xgb,onnx][0]={xgb_p[0,0]:.6f},{prob[0,0]:.6f}")
print("ONNX_CONVERT_OK")
