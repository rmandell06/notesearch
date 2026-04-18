import torch
import torch.nn as nn

class FeedForward(nn.Module):
  def __init__(self, d_model, d_ff, dropout):
    super(FeedForward, self).__init__()
    self.d_model = d_model
    self.dropout = nn.Dropout(dropout)

    self.linear_1 = nn.Linear(d_model, d_ff * 2)
    self.linear_2 = nn.Linear(d_ff, d_model)

  def forward(self, x):
    x = self.linear_1(x)
    
    x, gate = torch.chunk(x, 2, dim=-1)
    x = torch.relu(x)
    x = x * gate
    
    x = self.linear_2(x)
    x = self.dropout(x)
    return x

class Attention(nn.Module):
  def __init__(self, d_model, heads, dropout):
    super(Attention, self).__init__()
    self.d_model = d_model
    self.heads = heads

    self.q_linear = nn.Linear(d_model, d_model)
    self.k_linear = nn.Linear(d_model, d_model)
    self.v_linear = nn.Linear(d_model, d_model)
    self.n_linear = nn.Linear(d_model, d_model)

    self.dropout = nn.Dropout(dropout)
  
  def forward(self, x):
    key = self.k_linear(x)
    query = self.q_linear(x)
    value = self.v_linear(x)

    batch_size = x.shape[0]
    seq_len = x.shape[1]

    key = key.view(batch_size, seq_len, self.heads, self.d_model // self.heads)
    query = query.view(batch_size, seq_len, self.heads, self.d_model // self.heads)
    value = value.view(batch_size, seq_len, self.heads, self.d_model // self.heads)

    key = key.transpose(1, 2)
    query = query.transpose(1, 2)
    value = value.transpose(1, 2)

    result = query @ key.transpose(2, 3)

    result = result / (self.d_model // self.heads) ** 0.5

    result = torch.softmax(result, dim=3)

    result = self.dropout(result)

    result = result @ value

    result = result.transpose(1, 2)
    result = result.contiguous().view(batch_size, seq_len, self.d_model)
    result = self.n_linear(result)

    return result

class EncoderLayer(nn.Module):
  def __init__(self, d_model, heads, dropout, ff_dim):
    super(EncoderLayer, self).__init__()

    self.attention = Attention(d_model, heads, dropout)
    self.feed_forward = FeedForward(d_model, ff_dim, dropout)

    self.norm_1 = nn.LayerNorm(d_model)
    self.norm_2 = nn.LayerNorm(d_model)

  def forward(self, x):
    x = x + self.attention(self.norm_1(x))
    x = x + self.feed_forward(self.norm_2(x))
    return x

  
  class Encoder(nn.Module):
    def __init__(self, d_model, heads, dropout, ff_dim, num_layers, vocab_size, max_seq_len):
      super(Encoder, self).__init__()
     
      self.embedding = nn.Embedding(vocab_size, d_model)
      self.pos_encoding = nn.Embedding(max_seq_len, d_model)
      self.layers = nn.ModuleList([EncoderLayer(d_model, heads, dropout, ff_dim) for _ in range(num_layers)])
      self.norm = nn.LayerNorm(d_model)
      self.dropout = nn.Dropout(dropout)

    def forward(self, x):
      x = self.embedding(x)

      a = torch.arange(x.shape[1]).to(x.device)
      x = x + self.pos_encoding(a)
     
      x = self.dropout(x)
      for layer in self.layers:
        x = layer(x)
      x = self.norm(x)
      x = torch.mean(x, dim=1)
      return x





