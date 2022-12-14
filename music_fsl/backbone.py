from torchaudio.transforms import MelSpectrogram
from torch import nn
import torch 

class ConvBlock(nn.Module):
    """
    A convolutional block, consisting of a convolution, group normalization,
    ReLU activation, and max pooling.
    """

    def __init__(self, 
        in_channels, out_channels, 
        kernel_size, stride, padding, 
        num_groups, max_pool_size
    ):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding)
        self.gn = nn.GroupNorm(num_groups, out_channels)
        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool2d(max_pool_size)

    def forward(self, x):
        x = self.conv(x)
        x = self.gn(x)
        x = self.relu(x)
        x = self.maxpool(x)
        return x


class Backbone(nn.Module):
    """
    A fully convolutional model that produces 512-dimensional embeddings from audio samples. 
    
    Args:
        sample_rate (int): The sample rate of the input audio.
    """

    def __init__(self, sample_rate: int):
        super().__init__()
        self.sample_rate = sample_rate
        self.melspec = MelSpectrogram(
            n_mels=64, sample_rate=sample_rate
        )
        
        self.conv1 = ConvBlock(1, 32, 3, 1, 'same', 8, 2)
        self.conv2 = ConvBlock(32, 64, 3, 1, 'same',16, 2)
        self.conv3 = ConvBlock(64, 128, 3, 1, 'same', 32, 2)
        self.conv4 = ConvBlock(128, 256, 3, 1, 'same', 64, 2)
        self.conv5 = ConvBlock(256, 512, 1, 1, 'same', 128, 4)

    def forward(self, x: torch.Tensor):
        assert x.ndim == 3, "Expected a batch of audio samples shape (batch, channels, samples)"
        assert x.shape[1] == 1, "Expected a mono audio signal"

        x = self.melspec(x)

        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)

        # pool over the time dimension
        # squeeze the (t, f) dimensions
        x = x.mean(dim=-1)
        x = x.squeeze(-1).squeeze(-1) # (batch, 512)

        return x


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
