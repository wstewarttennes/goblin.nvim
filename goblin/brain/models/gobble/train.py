import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np
from typing import Dict, List
import json
from pathlib import Path

class SimpleTextModel(nn.Module):
    """A simple text classification model."""
    def __init__(self, vocab_size: int, embedding_dim: int, num_classes: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, 128)
        self.fc = nn.Linear(128, num_classes)
        
    def __call__(self, x):
        x = self.embedding(x)
        x, _ = self.lstm(x)
        # Take the last LSTM output
        x = x[:, -1, :]
        return self.fc(x)

class TextDataset:
    """Simple text dataset handler."""
    def __init__(self, texts: List[str], labels: List[int], max_len: int = 100):
        self.texts = texts
        self.labels = labels
        self.max_len = max_len
        self.vocab = self._build_vocab()
        
    def _build_vocab(self) -> Dict[str, int]:
        """Build a simple vocabulary from the texts."""
        vocab = {"<PAD>": 0, "<UNK>": 1}
        for text in self.texts:
            for word in text.lower().split():
                if word not in vocab:
                    vocab[word] = len(vocab)
        return vocab
    
    def encode_text(self, text: str) -> List[int]:
        """Convert text to integer sequence."""
        words = text.lower().split()
        encoded = [self.vocab.get(word, self.vocab["<UNK>"]) for word in words]
        # Pad or truncate to max_len
        if len(encoded) < self.max_len:
            encoded.extend([self.vocab["<PAD>"]] * (self.max_len - len(encoded)))
        return encoded[:self.max_len]
    
    def get_batch(self, batch_size: int):
        """Generate random batch of data."""
        indices = np.random.choice(len(self.texts), batch_size)
        batch_texts = [self.encode_text(self.texts[i]) for i in indices]
        batch_labels = [self.labels[i] for i in indices]
        return {
            'input': mx.array(batch_texts),
            'labels': mx.array(batch_labels)
        }

def train(model, dataset, optimizer, num_epochs: int, batch_size: int):
    """Training loop."""
    def loss_fn(model, batch):
        logits = model(batch['input'])
        return nn.losses.cross_entropy(logits, batch['labels'])
    
    # Training step function
    @mx.compile
    def train_step(model, batch):
        loss, grads = mx.value_and_grad(loss_fn)(model, batch)
        optimizer.update(model, grads)
        return loss
    
    # Training loop
    steps_per_epoch = len(dataset.texts) // batch_size
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        for step in range(steps_per_epoch):
            batch = dataset.get_batch(batch_size)
            loss = train_step(model, batch)
            epoch_loss += loss.item()
            
            if step % 10 == 0:
                print(f"Epoch {epoch+1}, Step {step}, Loss: {loss.item():.4f}")
        
        avg_loss = epoch_loss / steps_per_epoch
        print(f"Epoch {epoch+1} completed. Average loss: {avg_loss:.4f}")

def save_model(model, vocab, path: str):
    """Save model weights and vocabulary."""
    mx.savez(path + "_weights.npz", **model.parameters())
    with open(path + "_vocab.json", 'w') as f:
        json.dump(vocab, f)

def main():
    # Example dataset (replace with your own data)
    texts = [
        "this movie was great",
        "terrible waste of time",
        "absolutely loved it",
        "worst movie ever",
        "highly recommended",
        # Add more examples...
    ]
    labels = [1, 0, 1, 0, 1]  # 1 for positive, 0 for negative
    
    # Create dataset
    dataset = TextDataset(texts, labels, max_len=20)
    
    # Initialize model
    model = SimpleTextModel(
        vocab_size=len(dataset.vocab),
        embedding_dim=64,
        num_classes=2
    )
    
    # Setup optimizer
    optimizer = optim.Adam(learning_rate=0.001)
    
    # Train model
    train(model, dataset, optimizer, num_epochs=5, batch_size=2)
    
    # Save model
    save_model(model, dataset.vocab, "sentiment_model")

if __name__ == "__main__":
    main()
