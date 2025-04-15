import pickle

jumps = []
jumps.append({"airtime": 0.49, "height": 0})  # 1
jumps.append({"airtime": 0.49, "height": 0})  # 2
jumps.append({"airtime": 0.49, "height": 0})  # 3
jumps.append({"airtime": 0.49, "height": 0})  # 4
jumps.append({"airtime": 0.49, "height": 0})  # 5
jumps.append({"airtime": 0.49, "height": 0})  # 6
jumps.append({"airtime": 0.49, "height": 0})  # 7
jumps.append({"airtime": 0.49, "height": 0})  # 8
jumps.append({"airtime": 0.49, "height": 0})  # 9
jumps.append({"airtime": 0.49, "height": 0})  # 10
jumps.append({"airtime": 0.49, "height": 0})
jumps.append({"airtime": 0.49, "height": 0})
jumps.append({"airtime": 0.49, "height": 0})
jumps.append({"airtime": 0.49, "height": 0})

# Path to your file
file_path = "MichaelJumps.pkl"

# Load the data
with open(file_path, "rb") as f:
    data = pickle.load(f)

for i, jump in enumerate(data):
    print(
        f"Jump {i+1}: Airtime = {jump.metrics['airtime']:.3f} s | Height = {jump.metrics['height']:.3f} m"
    )
