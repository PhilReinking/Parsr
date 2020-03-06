import argparse
import os

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE, RandomOverSampler, ADASYN
from collections import Counter
from sklearn import metrics
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import RFECV
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn_porter import Porter

parser = argparse.ArgumentParser(description='Train a logistic regression model to recognize headings.')
parser.add_argument('dataset_dir', help='folder containing the .csv files generated by build_dataset.py')
parser.add_argument('out_dir', help='folder in which to save the trained model')
args = parser.parse_args()

dataset_dir = args.dataset_dir
paths = os.listdir(dataset_dir)
X = []
y = []

for path in paths:
    df = pd.read_csv(os.path.join(dataset_dir, path), header=0).drop('line', axis=1)

    if len(df) < 3:
        continue
    
    df['is_font_bigger'] = df['is_font_bigger'].apply(lambda x: 1 if x else 0)
    df['is_different_style'] = df['is_different_style'].apply(lambda x: 1 if x else 0)
    df['is_font_unique'] = df['is_font_unique'].apply(lambda x: 1 if x else 0)
    df['is_title_case'] = df['is_title_case'].apply(lambda x: 1 if x else 0)
    df['label'] = df['label'].apply(lambda x: 1 if x == 'heading' else 0)

    print(df.head())
    print(path)

    # convert dataframe to numpy array
    df_array = df.to_numpy()

    for arr in df_array:
        X.append(arr[:-1])
        y.append(arr[-1])


# Splitting dataset into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

# RandomOverSampler --- Resampling training set (to balance classes)
print('Original training set shape %s' % Counter(y_train))
X_train_res, y_train_res = RandomOverSampler(random_state=42).fit_resample(X_train, y_train)
print('Resampled training set shape %s' % Counter(y_train_res))

# SMOTE --- Resampling training set (to balance classes)
# print('Original training set shape %s' % Counter(y_train))
# X_train_res, y_train_res = SMOTE(random_state=42).fit_resample(X_train, y_train)
# print('Resampled training set shape %s' % Counter(y_train_res))

# ADASYN --- Resampling training set (to balance classes)
# print('Original training set shape %s' % Counter(y_train))
# X_train_res, y_train_res = ADASYN(random_state=42).fit_resample(X_train, y_train)
# print('Resampled training set shape %s' % Counter(y_train_res))


# fitting
grid = {"C":np.logspace(-3,3,7)}
clf_cv = GridSearchCV(LogisticRegression(), grid, cv=8).fit(X_train_res, y_train_res)
clf = LogisticRegression(C=clf_cv.best_params_['C'])
selector = RFECV(clf, step=1, cv=8, scoring=metrics.make_scorer(metrics.f1_score))
selector = selector.fit(X_train_res, y_train_res)


# overfitting
# X_res, y_res = RandomOverSampler(random_state=42).fit_resample(X, y)
# X_train2, X_test2, y_train2, y_test2 = train_test_split(X_res, y_res, test_size=0.3)
# grid = {"C":np.logspace(-3,3,7)}
# clf_cv = GridSearchCV(LogisticRegression(), grid, cv=8).fit(X_res, y_res)
# clf = LogisticRegression(C=clf_cv.best_params_['C'])
# selector = RFECV(clf, step=1, cv=8, scoring=metrics.make_scorer(metrics.f1_score))
# selector = selector.fit(X_res, y_res)

print(selector.support_)
print(selector.ranking_)

y_pred = selector.predict(X_test)

# clf.score(X, y)
print('f1:', metrics.f1_score(y_pred, y_test))
print('IoU:', metrics.jaccard_score(y_pred, y_test))
print('AuC:', metrics.roc_auc_score(y_pred, y_test))

porter = Porter(selector.estimator_, language='js')
output = porter.export(embed_data=True)

with open(os.path.join(args.out_dir, 'model.js'), mode='w+', encoding='utf8') as f:
    f.write('export ' + output)