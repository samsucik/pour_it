import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import numpy as np

y_tr = ["triangle","heart","circle","star","square","cross","triangle","heart","circle","star","square","cross","triangle","heart","circle","star","square","cross","triangle","heart","circle","star","square","cross","triangle","heart","circle","star","square","cross","triangle","heart","circle","star","square","cross","triangle","heart","circle","star","square","cross","triangle","heart","circle","star","square","cross","triangle","heart","circle","star","square","cross","triangle","heart","circle","star","square","cross"]
y_pred = ["triangle","triangle","triangle","square","circle","cross","square","triangle","triangle","cross","cross","cross","triangle","triangle","triangle","heart","circle","cross","square","cross","triangle","heart","circle","cross","triangle","square","square","square","circle","cross","square","triangle","heart","heart","circle","cross","triangle","triangle","triangle","heart","circle","cross","square","square","square","heart","circle","cross","triangle","triangle","triangle","heart","circle","square","square","cross","triangle","heart","circle","cross"]
labels = ['circle', 'cross', 'heart', 'square', 'star', 'triangle']

cm = confusion_matrix(y_tr, y_pred)
cm_norm = cm/cm.sum(axis=1)[:, np.newaxis]
plt.figure()
sns.heatmap(cm_norm, vmin=0., vmax=1., annot=True, xticklabels=labels, yticklabels=labels)
plt.title('Shape actual vs predicted (10cm distance)')
plt.ylabel('Actual shape')
plt.xlabel('Detected shape')
plt.show()