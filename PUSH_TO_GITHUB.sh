# Push to GitHub

## Step 1: Login to GitHub (if not done)
```bash
gh auth login
# Select: GitHub.com > HTTPS > Login with a web browser > Copy one-time code
```

## Step 2: Create repository and push
```bash
# Create new repository on GitHub
gh repo create efficient-funsearch --public --source=. --description "Sample-efficient FunSearch with duplicate code detection"

# Or push to existing repo:
# gh repo create jaycee6666/efficient-funsearch --public --source=. --description "Sample-efficient FunSearch with duplicate code detection"
```

## Step 3: After push, get Colab link
The Colab badge will be:
```markdown
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jaycee6666/efficient-funsearch/blob/main/notebooks/efficient_funsearch_colab.ipynb)
```
