import numpy as np,numpy.random
from hmmlearn import hmm
import os
from sklearn.ensemble import AdaBoostClassifier
import math
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
np.random.seed(42)
from sklearn.model_selection import KFold
import matplotlib.pyplot as plt
from sklearn.externals import joblib
import time
from sklearn.ensemble import AdaBoostClassifier

start_time = time.time()

fpaths = []
labels = []
opcodes = []

for f in os.listdir('opcodes'):
    for w in os.listdir('opcodes/'+f):
        fpaths.append('opcodes/'+f+'/'+w)
        labels.append(f)
        if f not in opcodes:
            opcodes.append(f)

print('malware name:',opcodes)

paths = []
index = 1

for f in os.listdir('benign'):
    paths.append('benign/'+f)

index1 =['mov', 'push', 'add', 'xor', 'sub', 'cmp', 'movzx', 'call', 'or', 'pop',
        'jmp', 'jz', 'and', 'retn', 'jnz', 'lea', 'adc', 'sbb', 'inc', 'dec',
        'test', 'xchg', 'imul', 'jnb', 'jb', 'shr', 'leave', 'jge', 'not', 'pusha']
testsample = []
inputfile = []
lengths = []
counter = 0
testsample1 = []
print("Loading data.....")

#load benigh opcodes
np.random.shuffle(paths)
for file in paths[0:200]:
    if os.path.getsize(file)>0:
        try:
            data = np.genfromtxt(file, dtype='str')
        except Exception:
            pass
        temp1 = []

        for i in data:
            num = 30
            if i in index1:
                num = index1.index(i)
                temp1.append(num)
            else:
                temp1.append(num)
        testsample1.append(temp1)
testsample1 = np.asarray(testsample1)
print("number of benign samples: ", len(testsample1))

#load malware opcodes
np.random.shuffle(fpaths)
for file in fpaths:
    try:
        data = np.genfromtxt(file, dtype='str')
    except Exception:
        pass
    temp1 = []
    for i in data:
        num = 30
        if i in index1:
            num = index1.index(i)
            temp1.append(num)
        else:
            temp1.append(num)
    #Only take 50% of samples due to large computation
    if counter < len(fpaths)*0.5:
        counter = counter + 1
    #print("Address : ", file)
        inputfile.append(temp1)
    else:
        testsample.append(temp1)
inputfile = np.asarray(inputfile)
print(" The number of malware samples :",len(inputfile))
print(" The number of test samples: ", len(testsample))


#kfold = KFold(5,True,1)

hidden_state = [2,3,5,10,30]
symbols = len(index1)+1

result = []#store malware scores after fit model
result1 = []#store benign scores after fit model
fpr = []#store fpr for each hidden_state
tpr = []#store tpr for each hidden_state
for hs in hidden_state:
    for i in range(1000):
        print("random restart: ", i+1)
        print("The number of Hidden States: ", hs)
        pi = np.random.dirichlet(np.ones(hs),size=1)
        A = np.random.dirichlet(np.ones(hs),size=hs)
        B = np.random.dirichlet(np.ones(symbols),size=hs)

        print("pi: ", pi)
        print("A : ", A)
        print("B : ", B)

        model = hmm.MultinomialHMM(n_components=hs,n_iter=100)
        model.startprob_ = pi[0]
        model.transmat_ = A
        model.emissionprob_ = B
        if (i == 0): bestmodel = model

        x = inputfile
        y = testsample
        z = testsample1
        inputSeq = []
        lengths = []
        for list in x:
            lengths.append(len(list))
        x = np.concatenate(x)
        x = np.reshape(x, (-1, 1))
        print(x.shape)
        model.fit(x, lengths)
        print(model.monitor_)
        #if model score better than bestmodel score, then....
        if (model.monitor_.history[1] > bestmodel.monitor_.history[1]):
            bestmodel = model
            joblib.dump(bestmodel, "hmm.pkl")
            #joblib.load("hmm.pkl")

    #compute and save malware scores using bestmodel
    for j in y:
        j = np.reshape(j, (-1, 1))
        result.append(bestmodel.score(j)/len(j))
    #compute and save benign scores using bestmodel
    for k in z:
        k = np.reshape(k, (-1, 1))
        result1.append(bestmodel.score(k)/len(k))
    #apply adaboost on the scores.
    test = np.concatenate((result,result1))
    test = np.reshape(test,(-1,1))
    y_ture = np.ones((len(result),),dtype=int)
    y_false = np.zeros((len(result1),),dtype=int)
    labels = np.append(y_ture,y_false)
    np.asarray(labels)
    print(labels)
    ada = AdaBoostClassifier(n_estimators=50,learning_rate=1)
    ada.fit(test, labels)
    print(ada.score(test,labels))#should give us mean of accurcy

    #plt scatter with all score points
    score = []
    for i in range(len(result)):
        plt.scatter(i,result[i],color='r')
        score.append(result[i])
    for j in range(len(result1)):
        plt.scatter(j,result1[j],color = 'g')
        score.append(result1[j])
    np.asarray(score)

    plt.show()

    #plt ROC cruve
    fpr[hs], tpr[hs], thresholds = roc_curve(labels,score,pos_label=1)
    roc_auc = auc(fpr,tpr)
    plt.figure()
    plt.plot(fpr, tpr, color='darkorange', lw=2, label='ROC curve (area = %0.2f)' % roc_auc)
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver operating characteristic')
    plt.legend(loc="lower right")
    plt.show()
    print("--- %s seconds ---" % round(time.time() - start_time,2))