import torch
import torch.nn.functional as F
import torch.nn as nn


def get_criterion(smooth=0.0, multilabel=False):
    if smooth > 0:
        if multilabel == False:
            criterion = LabelSmoothing(smooth)
        else:
            criterion = NLLMultiLabelSmooth(smooth)
    else:
        criterion = torch.nn.CrossEntropyLoss()
    return criterion

class LabelSmoothing(nn.Module):
    """
    NLL loss with label smoothing.
    """
    def __init__(self, smoothing=0.1):
        """
        Constructor for the LabelSmoothing module.
        :param smoothing: label smoothing factor
        """
        super(LabelSmoothing, self).__init__()
        self.confidence = 1.0 - smoothing
        self.smoothing = smoothing

    def forward(self, x, target):
        logprobs = torch.nn.functional.log_softmax(x, dim=-1)

        nll_loss = -logprobs.gather(dim=-1, index=target.unsqueeze(1))
        nll_loss = nll_loss.squeeze(1)
        smooth_loss = -logprobs.mean(dim=-1)
        loss = self.confidence * nll_loss + self.smoothing * smooth_loss
        return loss.mean()
    
class SoftArgmax1D(torch.nn.Module):
    """
    Implementation of a 1d soft arg-max function as an nn.Module, so that we can differentiate through arg-max operations.
    """
    def __init__(self, base_index=0, step_size=1, device='cpu', do_softmax=True):
        """
        The "arguments" are base_index, base_index+step_size, base_index+2*step_size, ... and so on for
        arguments at indices 0, 1, 2, ....
        Assumes that the input to this layer will be a batch of 1D tensors (so a 2D tensor).
        :param base_index: Remember a base index for 'indices' for the input
        :param step_size: Step size for 'indices' from the input
        """
        super(SoftArgmax1D, self).__init__()
        self.base_index = base_index
        self.step_size = step_size
        self.softmax = torch.nn.Softmax(dim=1)
        self.device = device
        self.do_softmax = do_softmax

    def forward(self, x):
        """
        Compute the forward pass of the 1D soft arg-max function as defined below:
        SoftArgMax(x) = \sum_i (i * softmax(x)_i)
        :param x: The input to the soft arg-max layer
        :return: Output of the soft arg-max layer
        """
        if self.do_softmax == True:
            smax = self.softmax(x)
        else:
            smax = x
        end_index = self.base_index + x.size()[1] * self.step_size
        indices = torch.arange(start=self.base_index, end=end_index, step=self.step_size).to(self.device).float()
        return torch.matmul(smax, indices.float())