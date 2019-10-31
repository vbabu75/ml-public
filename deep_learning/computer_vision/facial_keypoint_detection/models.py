## TODO: define the convolutional neural network architecture

import torch
import torch.nn as nn
import torch.nn.functional as F
# can use the below import should you choose to initialize the weights of your Net
import torch.nn.init as I

"""
Defines a neural network to do facial keypoint recognition. The class takes in a 
grayscale image and returns back 68 facial key points.
"""
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=1,out_channels=32,kernel_size=5,stride=1,padding=2)
        self.conv1bn = nn.BatchNorm2d(num_features=32)
        self.conv1a = nn.ReLU()
        self.conv1mp = nn.MaxPool2d((2,2),2)
        
        self.conv2 = nn.Conv2d(in_channels=32,out_channels=64,kernel_size=3,stride=1)
        self.conv2bn = nn.BatchNorm2d(num_features=64)
        self.conv2a = nn.ReLU()
        self.conv2mp = nn.MaxPool2d((2,2),2)
        
        self.conv3 = nn.Conv2d(in_channels=64,out_channels=96,kernel_size=5,stride=1)
        self.conv3bn = nn.BatchNorm2d(num_features=96)
        self.conv3a = nn.ReLU()
        self.conv3mp = nn.MaxPool2d((2,2),2)
        
        self.conv4 = nn.Conv2d(in_channels=96,out_channels=128,kernel_size=5,stride=1)
        self.conv4bn = nn.BatchNorm2d(num_features=128)
        self.conv4a = nn.ReLU()
        self.conv4mp = nn.MaxPool2d((2,2),2)
           
        
        self.fc1 = nn.Linear(128*10*10,1024)
        self.fc1bn = nn.BatchNorm1d(num_features=1024)
        self.fc1a = nn.ReLU()

        self.fc2 = nn.Linear(1024,1024)
        self.fc2bn = nn.BatchNorm1d(num_features=1024)        
        self.fc2a = nn.ReLU()
        
        self.fc3 = nn.Linear(1024,68*2)        
        
        self.convnet = [self.conv1,self.conv1bn,self.conv1a,self.conv1mp,
                        self.conv2,self.conv2bn,self.conv2a,self.conv2mp,
                        self.conv3,self.conv3bn,self.conv3a,self.conv3mp,
                        self.conv4,self.conv4bn,self.conv4a,self.conv4mp,
                       ]
        self.fcnet = [self.fc1,self.fc1bn,self.fc1a,
                      self.fc2,self.fc2bn,self.fc2a,
                      self.fc3
                     ]
    def forward(self, x):
        for layer in self.convnet:
            x = layer(x)
        x = x.view(x.shape[0],-1)
        for layer in self.fcnet:
            x = layer(x)
        return x
