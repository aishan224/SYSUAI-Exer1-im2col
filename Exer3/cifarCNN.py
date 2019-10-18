import torch
import torch.nn as nn
import torch.nn.functional as F 
import torch.optim as optim 
import torch.utils.data as Data  # to make Loader
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt 
import os
import numpy as np 
import time
import csv

# hyper Parameters
EPOCH = 10
BATCH_SIZE = 100
LR = 0.001
DOWNLOAD_CIFAR10 = False
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu") # the device used to calc
# print(device)
transform = transforms.Compose(
    [transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
)

train_data = torchvision.datasets.CIFAR10(
    root='./data',
    train=True,
    download=DOWNLOAD_CIFAR10,
    transform=transform
)
train_loader = Data.DataLoader(
    train_data,
    batch_size=BATCH_SIZE,
    shuffle=True,
    # num_workers=2 # ready to be commented(windows)
)

test_data = torchvision.datasets.CIFAR10(
    root='./data',
    train=False,
    download=DOWNLOAD_CIFAR10,
    transform=transform,
)
test_loader = Data.DataLoader(
    test_data,
    batch_size=BATCH_SIZE,
    shuffle=False,
    # num_workers=2
)

classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

# show some pics
# def imshow(img):
#     img = img /2 +0.5
#     npimg = img.numpy()
#     plt.imshow(np.transpose(npimg, (1,2,0)))
#     plt.show()

# dataiter = iter(train_loader)
# images, labels = dataiter.next()
# imshow(torchvision.utils.make_grid(images))
# print(' '.join('%5s' % classes[labels[j]] for j in range(4)))


# define the Net
class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)

        self.fc1 = nn.Linear(16*5*5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10) # result is ten kinds of item

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16*5*5) # reshape to 16*5*5 to fc
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        output = self.fc3(x)
        return output

cnn = CNN()
cnn.to(device)  # 1
# print(cnn)

# save or show losses
losses = [] # record losses
def save_losses(losses):
    t = np.arange(len(losses))
    plt.plot(t, losses)
    plt.savefig('loss.png')
    # plt.show()

# define loss function and optimizer
optimizer = optim.Adam(cnn.parameters())
loss_func = nn.CrossEntropyLoss()
state = {'cnn': cnn.state_dict(), 'optimizer': optimizer.state_dict()}

# training
start = time.time()
model_save_path = './data/cifar-10-batches-py/saved_model/'
model_path = model_save_path + 'saved_model.pth'

def train():
    global losses
    for epoch in range(EPOCH):
        running_loss = 0.0
        for step, (inputs, labels) in enumerate(train_loader, 0):
            # inputs, labels = data[0].to(device), data[1].to(device)
            inputs = inputs.to(device)  # 2
            labels = labels.to(device)
            
            optimizer.zero_grad()
            output = cnn(inputs)
            loss = loss_func(output, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            if step % 100 == 99:
                loss_num = running_loss / 100
                losses.append(loss_num)
                print('|epoch: %d, step: %5d| -> loss: %.3f|' %(epoch+1, step+1, loss_num))
                running_loss = 0.0
    
    # save losses
    save_losses(losses)

# training
if not os.path.exists(model_save_path):
    os.makedirs(model_save_path)
    
if os.path.isfile(model_path): # if there has been the file, load and train on it
    cnn.load_state_dict(torch.load(model_path)['cnn'])
    optimizer.load_state_dict(torch.load(model_path)['optimizer'])
    print("Loaded model parameters from disk successfully!")
    train()
    print("Training Finished!")
    torch.save(state, model_path)
    print("Model Saved Complete!")
else:
    train()
    print("Training Finished!")
    torch.save(state, model_path)
    print("Model Saved Complete!")

end = time.time()
print('takes:', end-start,'s')

# test and get accuracy
correct_time = time.time()
classes_correct = [0 for i in range(10)]
classes_total = [0 for i in range(10)]
pass_total = 0
train_total = 50000
test_total = 10000
# test train_data
print("-----Test Train results-----")
with torch.no_grad():
    for (images, labels) in train_loader:
        # images, labels = data[0].to(device), data[1].to(device)
        images = images.to(device)  # 3
        labels = labels.to(device)
        output = cnn(images)
        _, prediction = torch.max(output, 1)
        c = (prediction == labels).squeeze()
        for i in range(BATCH_SIZE):
            label = labels[i]
            classes_correct[label] += c[i].item()
            classes_total[label] += 1

accNow = []
for i in range(len(classes)):
    print("%3d of %4d passed | accuracy of %5s -> %2d %%" % (classes_correct[i], classes_total[i], classes[i],round(100*classes_correct[i]/classes_total[i])))
    pass_total += classes_correct[i]
    accNow.append(str(round(100*classes_correct[i]/classes_total[i])) + '%')
accNow.append(str(round(100*pass_total/train_total)) + '%')
print("%3d of %4d passed | total accuracy is -> %2d %%" % (pass_total, train_total, round(100*pass_total/train_total)))
print()

with open('trainAccHistory.csv', 'a+', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(accNow)


# test test_data
pass_total = 0
classes_correct = [0 for i in range(10)]
classes_total = [0 for i in range(10)]
print("-----Test Test results-----")
with torch.no_grad():
    for (images, labels) in test_loader:
        # images, labels = data[0].to(device), data[1].to(device)
        images = images.to(device)  # 3
        labels = labels.to(device)
        output = cnn(images)
        _, prediction = torch.max(output, 1)
        c = (prediction == labels).squeeze()
        for i in range(BATCH_SIZE):
            label = labels[i]
            classes_correct[label] += c[i].item()
            classes_total[label] += 1

accNow = []
for i in range(len(classes)):
    print("%3d of %4d passed | accuracy of %5s -> %2d %%" % (classes_correct[i], classes_total[i], classes[i],round(100*classes_correct[i]/classes_total[i])))
    pass_total += classes_correct[i]
    accNow.append(str(round(100*classes_correct[i]/classes_total[i])) + '%')
accNow.append(str(round(100*pass_total/test_total)) + '%')
print("%3d of %4d passed | total accuracy is -> %2d %%" % (pass_total, test_total, round(100*pass_total/test_total)))
print()

with open('TestAccHistory.csv', 'a+', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(accNow)

now = time.time()
print('test takes:', now-correct_time,'s')

