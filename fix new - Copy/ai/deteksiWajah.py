import torch
from torchvision import transforms
from PIL import Image
import cv2
import os  # Added missing import

class EmotionDetector:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model()
        self.labels = ['marah', 'jijik', 'takut', 'senang', 'sedih', 'kaget', 'netral']
        self.transform = transforms.Compose([
            transforms.Grayscale(),
            transforms.Resize((48, 48)),
            transforms.ToTensor()
        ])
    
    def _load_model(self):
        class SmallEmotionCNN(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.conv = torch.nn.Sequential(
                    torch.nn.Conv2d(1, 32, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
                    torch.nn.Conv2d(32, 64, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
                )
                self.fc = torch.nn.Sequential(
                    torch.nn.Linear(64 * 12 * 12, 128), torch.nn.ReLU(),
                    torch.nn.Linear(128, 7)  # Added missing closing parenthesis
                )
            def forward(self, x):
                x = self.conv(x)
                x = x.view(x.size(0), -1)
                return self.fc(x)
        
        model = SmallEmotionCNN().to(self.device)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "model", "emotion_model.pth")
                                #  map_location=self.device)
        model.eval()
        return model
    
    def detect(self, img_data):
        if isinstance(img_data, Image.Image):
            img = img_data
        else:
            img = Image.fromarray(cv2.cvtColor(img_data, cv2.COLOR_BGR2RGB))
        
        img = img.convert('L')
        t = self.transform(img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            out = self.model(t)
            _, p = torch.max(out, 1)
            
        return self.labels[p.item()]