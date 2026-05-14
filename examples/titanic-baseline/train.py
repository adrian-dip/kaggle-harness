import os
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

SEED = int(os.environ.get("SEED", 42))
DATA = Path("/data/competitions/titanic")
OUT = Path("/out")

train = pd.read_csv(DATA / "train.csv")
test = pd.read_csv(DATA / "test.csv")

features = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare"]
train["Sex"] = (train["Sex"] == "male").astype(int)
test["Sex"] = (test["Sex"] == "male").astype(int)

X = train[features].fillna(0)
y = train["Survived"]
X_test = test[features].fillna(0)

clf = RandomForestClassifier(n_estimators=100, random_state=SEED)
clf.fit(X, y)

preds = clf.predict(X_test)
submission = pd.DataFrame({"PassengerId": test["PassengerId"], "Survived": preds})
submission.to_csv(OUT / "submission.csv", index=False)
print("Done. submission.csv written.")
