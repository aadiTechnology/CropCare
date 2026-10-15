import numpy as np
from ai_edge_litert.interpreter import Interpreter

path = r"c:\Users\lenovo\AadiTech\Product\CropDiseaseDetection\mobile\assets\models\tomato\model.tflite"
interpreter = Interpreter(model_path=path)
interpreter.allocate_tensors()
inputs = interpreter.get_input_details()
outputs = interpreter.get_output_details()
print("INPUT", {k: inputs[0][k] for k in ("name", "shape", "shape_signature", "dtype", "index")})
print("OUTPUT", {k: outputs[0][k] for k in ("name", "shape", "shape_signature", "dtype", "index")})

sample = np.zeros(inputs[0]["shape"], dtype=np.float32)
sample[..., 0] = 180
sample[..., 1] = 160
sample[..., 2] = 40
interpreter.set_tensor(inputs[0]["index"], sample)
interpreter.invoke()
probs = interpreter.get_tensor(outputs[0]["index"]).reshape(-1)
print("len", probs.shape, "sum", float(probs.sum()), "finite", bool(np.isfinite(probs).all()))
print("values", np.array2string(probs, precision=6))
print("argmax", int(probs.argmax()), float(probs.max()))
