import torch
print(torch.__version__)
print(torch.version.cuda)


if torch.cuda.is_available():
    accelerator = "gpu"
    print(torch.version.cuda)
else:
    accelerator = "cpu"
    print("WARNING: GPU not available, using CPU instead")
