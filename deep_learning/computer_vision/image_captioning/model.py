import torch
import torch.nn as nn
import torchvision.models as models
import numpy as np


class EncoderCNN(nn.Module):
    def __init__(self, embed_size):
        super(EncoderCNN, self).__init__()
        resnet = models.resnet50(pretrained=True)
        for param in resnet.parameters():
            param.requires_grad_(False)
        
        modules = list(resnet.children())[:-1]
        self.resnet = nn.Sequential(*modules)
        self.embed = nn.Linear(resnet.fc.in_features, embed_size)

    def forward(self, images):
        features = self.resnet(images)
        features = features.view(features.size(0), -1)
        features = self.embed(features)
        return features
    

class DecoderRNN(nn.Module):
    def __init__(self, embed_size, hidden_size, vocab_size, num_layers=1):
        super(DecoderRNN, self).__init__()
        self.embeddings = nn.Embedding(vocab_size,embed_size)
        self.lstm = nn.LSTM(embed_size, hidden_size,num_layers=num_layers,batch_first=True)
        self.linear = nn.Linear(hidden_size,vocab_size)
        
    
    def forward(self, features, captions):
        # We need to construct a tensor with the image features as the first element of sequence and the embedding
        # of the captions as the subsequent elements of the sequence. The end marker of the caption can be ignored.
        embedds = self.embeddings(captions[:,:-1])
        x = torch.cat((features.unsqueeze(1),embedds),1)

        hidden,cell_state = self.lstm(x)
        output = self.linear(hidden)
        return output

    def sample(self, inputs, states=None, max_len=20):
        " accepts pre-processed image tensor (inputs) and returns predicted sentence (list of tensor ids of length max_len) "
        with torch.no_grad():
            inputs = inputs.squeeze(1)
            caption=[]
            count = 0
            token = int(0)
            while token != 1 and count < max_len:
                caption.append(token)
                caption_with_end = caption+[1]
                captionTensor = torch.tensor(np.array(caption_with_end,dtype=np.int)).unsqueeze(0).to(inputs.device)
                output = self.forward(inputs,captionTensor)
                output = np.argmax(output.cpu().squeeze(0).numpy(),1)
                token = int(output[-1])
                count += 1
            return caption[1:]