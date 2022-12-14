
import torch
import numpy as np
from torch import nn
import pytorch_lightning as pl
from torchmetrics import Accuracy

from music_fsl.backbone import Backbone
from music_fsl.data import TinySOL, EpisodeDataset
from music_fsl.protonet import PrototypicalNet

TRAIN_INSTRUMENTS = [
    'French Horn', 
    'Violin', 
    'Flute', 
    'Contrabass', 
    'Trombone', 
    'Cello', 
    'Clarinet in Bb', 
    'Oboe',
    'Accordion'
]

TEST_INSTRUMENTS = [
    'Bassoon',
    'Viola',
    'Trumpet in C',
    'Bass Tuba',
    'Alto Saxophone'
]

class FewShotLearner(pl.LightningModule):

    def __init__(self, 
        protonet: nn.Module, 
        learning_rate: float = 1e-3,
    ):
        super().__init__()
        self.save_hyperparameters(ignore=["protonet"])
        self.protonet = protonet
        self.learning_rate = learning_rate

        self.loss = nn.CrossEntropyLoss()
        self.metrics = nn.ModuleDict({
            'accuracy': Accuracy()
        })

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.learning_rate)
        return optimizer

    def step(self, batch, batch_idx, tag: str):
        support, query = batch

        logits = self.protonet(support, query)
        loss = self.loss(logits, query["target"])

        output = {"loss": loss}
        for k, metric in self.metrics.items():
            output[k] = metric(logits, query["target"])

        for k, v in output.items():
            self.log(f"{k}/{tag}", v)
        return output

    def training_step(self, batch, batch_idx):
        return self.step(batch, batch_idx, "train")
    
    def validation_step(self, batch, batch_idx):
        return self.step(batch, batch_idx, "val")

    def test_step(self, batch, batch_idx):
        return self.step(batch, batch_idx, "test")


def train(
        sample_rate: int = 16000,
        n_way: int = 5,
        n_support : int = 5,
        n_query: int = 20,
        n_train_episodes: int = int(100e3),
        n_val_episodes: int = 100,
        num_workers: int = 10,
    ):
    """
    The train function trains a few-shot learning model on the TinySOL dataset. It takes the following parameters:

    Args:
        sample_rate (int): The sample rate of the audio data. 
            Default: 16000.
        n_way (int): The number of classes to sample per episode.
            Default: 5.
        n_support (int): The number of support examples per class.
        n_query (int): The number of samples per class to use as query.
            Default: 20.
        n_train_episodes (int): The number of episodes to generate for training.
            Default: 100000.
        n_val_episodes (int): The number of episodes to generate for validation.
            Default: 100.
        num_workers (int): The number of worker threads to use for data loading.
            Default: 10.

    The function initializes the datasets and samplers, builds the model, and trains it using PyTorch Lightning.
    """
    # initialize the datasets
    train_data = TinySOL(
        instruments=TRAIN_INSTRUMENTS, 
        sample_rate=sample_rate
    )

    val_data = TinySOL(
        instruments=TEST_INSTRUMENTS, 
        sample_rate=sample_rate
    )

    # initialize the episode datasets
    train_episodes = EpisodeDataset(
        dataset=train_data, 
        n_way=n_way, 
        n_support=n_support,
        n_query=n_query, 
        n_episodes=n_train_episodes
    )

    val_episodes = EpisodeDataset(
        dataset=val_data, 
        n_way=n_way, 
        n_support=n_support,
        n_query=n_query, 
        n_episodes=n_val_episodes
    )

    # initialize the dataloaders
    from torch.utils.data import DataLoader
    train_loader = DataLoader(
        train_episodes, 
        batch_size=None,
        num_workers=num_workers
    )

    val_loader = DataLoader(
        val_episodes, 
        batch_size=None,
        num_workers=num_workers
    )

    # build models
    backbone = Backbone(sample_rate=sample_rate)
    protonet = PrototypicalNet(backbone)
    learner = FewShotLearner(protonet)
    print(learner)

    # set up the trainer
    from pytorch_lightning.loggers import TensorBoardLogger
    from pytorch_lightning.profiler import SimpleProfiler

    trainer = pl.Trainer(
        gpus=1 if torch.cuda.is_available() else 0,
        max_epochs=1,
        log_every_n_steps=1, 
        val_check_interval=50,
        profiler=SimpleProfiler(
            filename="profile.txt",
        ), 
        logger=TensorBoardLogger(
            save_dir=".",
            name="logs"
        ), 
    )

    # train!
    trainer.fit(learner, train_loader, val_dataloaders=val_loader)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--sample_rate", type=int, default=16000)
    parser.add_argument("--n_way", type=int, default=5)
    parser.add_argument("--n_support", type=int, default=5)
    parser.add_argument("--n_query", type=int, default=20)
    parser.add_argument("--n_train_episodes", type=int, default=int(100e3))
    parser.add_argument("--n_val_episodes", type=int, default=100)
    parser.add_argument("--num_workers", type=int, default=10)
    args = parser.parse_args()

    train(**vars(args))