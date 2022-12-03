from setuptools import setup, find_packages
from pathlib import Path


setup(
    name='music_fsl',
    version='0.1.2',
    description='Few-shot learning for music instrument recognition using PyTorch',
    author='Hugo Flores García',
    author_email='hugofloresgarcia@u.northwestern.edu',
    url='https://blog.godatadriven.com/setup-py',
    packages=find_packages(include=['music_fsl']),
    install_requires=[
        # data
        "mirdata",
        "librosa",

        # training
        "torch",
        "numpy",
        "torchaudio",
        "torchmetrics",
        "pytorch-lightning",
        "tensorboard",
        "argbind",

        # display
        "torchvision",
        "sklearn",
        "umap-learn",
        "pandas",
        "plotly",
        "kaleido",
    ],
)