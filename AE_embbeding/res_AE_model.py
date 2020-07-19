import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as weight_init
from torch.autograd import Variable
input_dim = 105729
embedding_dim = 30
def activation(input, kind):
  #print("Activation: {}".format(kind))
  if kind == 'selu':
    return F.selu(input)
  elif kind == 'relu':
    return F.relu(input)
  elif kind == 'relu6':
    return F.relu6(input)
  elif kind == 'sigmoid':
    return torch.sigmoid(input)
  elif kind == 'tanh':
    return F.tanh(input)
  elif kind == 'elu':
    return F.elu(input)
  elif kind == 'lrelu':
    return F.leaky_relu(input)
  elif kind == 'swish':
    return input*F.sigmoid(input)
  elif kind == 'none':
    return input
  else:
    raise ValueError('Unknown non-linearity type')

class res_AutoEncoder(nn.Module):
  def __init__(self, layer_sizes, is_res = True, nl_type='selu', dp_drop_prob=0.0, last_layer_activations='sigmoid'):
    super(res_AutoEncoder, self).__init__()
    self.is_res = is_res
    self.layer_sizes = layer_sizes
    self._dp_drop_prob = dp_drop_prob
    self._last_layer_activations = last_layer_activations

    self._last = len(layer_sizes) - 2
    self._nl_type = nl_type

    self.emb = nn.Embedding(num_embeddings = input_dim + 1, embedding_dim = embedding_dim, padding_idx = input_dim)

    self.MLP_list = nn.ModuleList([nn.Linear(layer_sizes[i], layer_sizes[i+1]) for i in range(len(layer_sizes)-1)])
    self.res_list = nn.ModuleList([nn.Linear(layer_sizes[i*2], layer_sizes[i*2+2]) for i in range(int((len(layer_sizes)-1)/2))])
    
    weight_init.xavier_uniform_(self.emb.weight)
    weight_init.zeros_(self.emb.weight[input_dim])
    for L in self.MLP_list:
      weight_init.xavier_uniform_(L.weight)
      L.bias.data.fill_(0.)
    for L in self.res_list:
      weight_init.xavier_uniform_(L.weight)
      L.bias.data.fill_(0.)

    self.MLP_bn = nn.ModuleList([torch.nn.BatchNorm1d(layer_sizes[i+1]) for i in range(len(layer_sizes)-2)])
    if self._dp_drop_prob>0:
      self.dp = nn.Dropout(self._dp_drop_prob)

  def forward(self, x):
    #x is a tensor of indices 
    x = self.emb(x).reshape(x.shape[0],-1)
    MLP_output = x
    for idx, L in enumerate(self.MLP_list):
      if idx == len(self.MLP_list)-1:
        x = L(x)
        break
      if idx % 2 == 0:
        x = activation(L(x),self._nl_type)
        if idx != (len(self.MLP_list)-1):
          x = self.MLP_bn[idx](x)
      else:
        x = activation(L(x),self._nl_type)
        if x.shape[1]==MLP_output.shape[1] and self.is_res:
          x = x + MLP_output #chk if idx-1 = len(MLP_output)-2
        MLP_output = x
      if idx == int(len(self.MLP_list)/2)-1 and self._dp_drop_prob>0:
        x = self.dp(x)
      '''if idx == int(len(self.layer_sizes)/2):
        x = self.dp(x)'''
    return activation(x, self._last_layer_activations)