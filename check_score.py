import numpy as np
for i in range(5):
    try:
        d = np.load(f'/home/qntmqrks/rbx1_design/Phase13_Chai1/rfd_binder_38/scores.model_idx_{i}.npz')
        print(f"Model {i}:")
        print("  Keys:", d.files)
        for k in d.files:
            print(f"  {k}: {d[k]}")
    except Exception as e:
        print(e)
