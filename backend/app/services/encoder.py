import json
from pathlib import Path

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
    x = torch.nn.functional.silu(x)
    x = x * gate

    x = self.linear_2(x)
    x = self.dropout(x)
    return x

class Attention(nn.Module):
  def __init__(self, d_model, heads, dropout, max_seq_len, rope_base=10000.0):
    super(Attention, self).__init__()
    self.d_model = d_model
    self.heads = heads
    self.head_dim = d_model // heads

    self.q_linear = nn.Linear(d_model, d_model)
    self.k_linear = nn.Linear(d_model, d_model)
    self.v_linear = nn.Linear(d_model, d_model)
    self.n_linear = nn.Linear(d_model, d_model)

    self.dropout = nn.Dropout(dropout)

    # Precompute RoPE frequencies
    freqs = 1.0 / (rope_base ** (torch.arange(0, self.head_dim, 2).float() / self.head_dim))
    positions = torch.arange(max_seq_len).float()
    angles = torch.outer(positions, freqs)
    self.register_buffer('rope_cos', torch.cos(angles))
    self.register_buffer('rope_sin', torch.sin(angles))

  def apply_rope(self, x):
    """Apply rotary position embeddings. x shape: [batch, heads, seq_len, head_dim]"""
    seq_len = x.shape[2]

    # Split into even/odd dimensions
    x1 = x[..., ::2]
    x2 = x[..., 1::2]

    # Get cos/sin for current sequence length
    cos = self.rope_cos[:seq_len].unsqueeze(0).unsqueeze(0)
    sin = self.rope_sin[:seq_len].unsqueeze(0).unsqueeze(0)

    # Apply rotation and interleave back
    rotated = torch.stack([
        x1 * cos - x2 * sin,
        x1 * sin + x2 * cos
    ], dim=-1).flatten(-2)

    return rotated

  def forward(self, x):
    key = self.k_linear(x)
    query = self.q_linear(x)
    value = self.v_linear(x)

    batch_size = x.shape[0]
    seq_len = x.shape[1]

    key = key.view(batch_size, seq_len, self.heads, self.head_dim)
    query = query.view(batch_size, seq_len, self.heads, self.head_dim)
    value = value.view(batch_size, seq_len, self.heads, self.head_dim)

    key = key.transpose(1, 2)
    query = query.transpose(1, 2)
    value = value.transpose(1, 2)

    # Apply RoPE to query and key (not value)
    query = self.apply_rope(query)
    key = self.apply_rope(key)

    result = query @ key.transpose(2, 3)

    result = result / self.head_dim ** 0.5

    result = torch.softmax(result, dim=3)

    result = self.dropout(result)

    result = result @ value

    result = result.transpose(1, 2)
    result = result.contiguous().view(batch_size, seq_len, self.d_model)
    result = self.n_linear(result)

    return result

class EncoderLayer(nn.Module):
  def __init__(self, d_model, heads, dropout, ff_dim, max_seq_len):
    super(EncoderLayer, self).__init__()

    self.attention = Attention(d_model, heads, dropout, max_seq_len)
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

    self.config = {
      "d_model": d_model,
      "heads": heads,
      "dropout": dropout,
      "ff_dim": ff_dim,
      "num_layers": num_layers,
      "vocab_size": vocab_size,
      "max_seq_len": max_seq_len,
    }

    self.embedding = nn.Embedding(vocab_size, d_model)
    self.layers = nn.ModuleList([EncoderLayer(d_model, heads, dropout, ff_dim, max_seq_len) for _ in range(num_layers)])
    self.norm = nn.LayerNorm(d_model)
    self.dropout = nn.Dropout(dropout)

  def forward(self, x):
    x = self.embedding(x)
    x = self.dropout(x)
    for layer in self.layers:
      x = layer(x)
    x = self.norm(x)
    x = torch.mean(x, dim=1)
    return x

  def save(self, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    torch.save(self.state_dict(), directory / "encoder.pt")
    with open(directory / "config.json", "w") as f:
      json.dump(self.config, f, indent=2)

  @classmethod
  def load(cls, directory, map_location=None):
    directory = Path(directory)
    with open(directory / "config.json") as f:
      config = json.load(f)
    model = cls(**config)
    model.load_state_dict(torch.load(directory / "encoder.pt", map_location=map_location))
    model.eval()
    return model
